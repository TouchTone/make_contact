#!/usr/bin/python

# Make a contact sheet for a directory containing images.

# This is copy-n-pasted from another system, so apologies for it being a little messy...


import os, sys, glob, re, math, random, fnmatch, copy, json, time
import zipfile
from StringIO import StringIO
from PIL import Image, ImageDraw, ImageFont
import argparse


class AbortException(Exception):
    pass

# Helpers

def enum(*sequential, **named):
    if isinstance(sequential[0], tuple):
        enums = dict(zip([s[0] for s in sequential], range(len(sequential))), **named)
        reverse = dict((value, key) for key, value in enums.iteritems())
        enums['attribs'] = dict(zip([s[0] for s in sequential], [s[1:] for s in sequential]))
        enums['enum_attribs'] = [s[1:] for s in sequential]
    else:
        enums = dict(zip(sequential, range(len(sequential))), **named)
        reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    enums['count'] = len(enums)
    return type('Enum', (), enums)
    
LogLevels = enum("FATAL", "ERROR", "WARNING", "INFO", "PROGRESS", "DEBUG")

logLevel = LogLevels.INFO
errorlog = None
logpipe = None


def log(level, msg):
    if logLevel >= LogLevels.DEBUG and level == LogLevels.PROGRESS:
        # Don't let progress mess up debug log
        return

    if not logpipe is None:
        logpipe(level, msg)
        return

    if level <= logLevel:
        sys.stderr.write(msg)
        sys.stderr.flush()
    if level <= LogLevels.ERROR and errorlog:
        errorlog.write(msg)
        errorlog.flush()
    if level == LogLevels.FATAL:
        sys.stderr.write("Encountered fatal error, aborting!")
        sys.exit(1)


# Helper function for quick pre-resizing down powers of two, to about 4*target size
def preresize(img, box):
    factor = 1
    while img.size[0]/factor > 4*box[0] and img.size[1]/factor > 4*box[1]:
        factor *=2
    if factor > 1:
        img.thumbnail((img.size[0]/factor, img.size[1]/factor), Image.NEAREST)
    return img, factor


# Fast image resize for thumbnails
# based on http://united-coders.com/christian-harms/image-resizing-tips-every-coder-should-know
def resize(img, box, fit = False, center = True, left = False, out = None, background = (255,255,255)):
    '''Downsample the image.
   @param img: Image -  an Image-object to be resized
   @param box: tuple(x, y) - the bounding box of the result image
   @param fit: boolean - crop the image to fill the box
   @param out: file-like-object - save the image into the output stream
   @param center: boolean - center the image in the box
   '''

    try:
        fn = img.filename
    except IndexError:
        fn = None

    #preresize image with factor 2, 4, 8 and fast algorithm
    #Don't go down as far as possible, leave some pixels for anitaliasing 
    preresize(img, box)
 
    # Crop to center part of image that fits aspect ratio
    if fit:
        x1 = y1 = 0
        x2, y2 = img.size
        wRatio = float(x2)/box[0]
        hRatio = float(y2)/box[1]
        if hRatio > wRatio:
            y1 = int(y2/2-box[1]*wRatio/2)
            y2 = int(y2/2+box[1]*wRatio/2)
        else:
            x1 = int(x2/2-box[0]*hRatio/2)
            x2 = int(x2/2+box[0]*hRatio/2)
        print "Fit: is=(%d,%d) wr=%f hf=%f box=(%d,%d) out=(%d,%d,%d,%d)" % (img.size[0], img.size[1], wRatio, hRatio, box[0], box[1] ,x1,y1,x2,y2)
        img = img.crop((x1,y1,x2,y2))
 
    # Crop to left part of image that fits aspect ratio, scale vertical to fit
    elif left:
        x1 = y1 = 0
        wRatio = 1.0 * box[0] / img.size[0]
        hRatio = 1.0 * box[1] / img.size[1]
        
        if hRatio > wRatio:
            if hRatio > 1:
                hRatio = 1
            x2 = int(img.size[0] * hRatio)
            y2 = int(img.size[1] * hRatio)
            y1 = (box[1] - y2) / 2
           
        else:
            x2 = int(img.size[0] * hRatio)
            y2 = int(img.size[1] * hRatio)
            x1 = (box[0] - x2) / 2

        img = img.resize((x2,y2), Image.ANTIALIAS) # Scaling up doesn't work with thumbnail

        if x2 > box[0] or y2 > box[1]:
            img = img.crop((0,0,min(box[0],x2), min(box[1],y2)))
       
        if img.size != box:
            i2 = Image.new("RGB", box, background)
            i2.paste(img, (x1,y1))

            img = i2

    # For centering, scale into box with correct aspect and paste into middle
    elif center:
        x1 = y1 = 0
        wRatio = 1.0 * box[0] / img.size[0]
        hRatio = 1.0 * box[1] / img.size[1]
        if hRatio > wRatio:
            x2 = int(img.size[0] * wRatio)
            y2 = int(img.size[1] * wRatio)
            y1 = (box[1] - y2) / 2
        else:
            x2 = int(img.size[0] * hRatio)
            y2 = int(img.size[1] * hRatio)
            x1 = (box[0] - x2) / 2
        
        img = img.resize((x2,y2), Image.ANTIALIAS)

        i2 = Image.new("RGB", box, background)
        i2.paste(img, (x1,y1))
        
        img = i2
   
    else:  
        # Resize the image with best quality algorithm ANTI-ALIAS
        # Don't use thumbnail here, it messes up the size by 1 or 2 pixels
        img = img.resize(box, Image.ANTIALIAS)
 
    if out != None:
        #save it into a file-like object
        img.save(out, "JPEG", quality=75)

    if not fn is None:
        setattr(img, "filename", fn)

    return img


# Helper routine for layout. Lay out a list of images to fit a given width and (optional) height

def layoutRow(pics, width, height = -1, border = 0, thimgsize = 150):
    # How wide can it be?
    effw = width - border * (len(pics) + 1)

    scales = []

    # How wide is the row if all pics are scaled to thimgsize height?
    iw = 0
    for p in pics:
        pf = thimgsize / float(p.size[1])
        if p.size[0] * pf > width:
            pf = width / float(p.size[0])

        scales.append(pf)
        iw += int(pf * p.size[0])

    # Adjust scale factor to match width
    factor = effw / float(iw)
    th = int(thimgsize * factor)

    # Calculate sizes based on factor
    tsizes = []
    iw = 0
    for i,p in enumerate(pics):
        ts = (int((p.size[0]) * scales[i] * factor), th)
        iw += ts[0]
        tsizes.append(ts)

    # Adjustment pixel sizes to match width exactly
    todo = effw - iw
    ind = 0
    if todo > 0:
        while todo > 0:
            tsizes[ind] = (tsizes[ind][0] + 1, tsizes[ind][1])
            todo = todo - 1
            ind = ind + 1
            if ind >= len(pics):
                ind = 0
    else:
        while todo < 0:
            tsizes[ind] = (tsizes[ind][0] - 1, tsizes[ind][1])
            todo = todo + 1
            ind = ind + 1
            if ind >= len(pics):
                ind = 0

    # Return results
    return tsizes, th, factor, effw - iw


labelfont = None
labelfontheight = 0

def drawLabel(im, draw, text, pos, size, options):
    global labelfont, labelfontheight

    if labelfont is None:
        if not os.path.isfile(options['font']):
            options['font'] = os.path.join(basedir, options['font'])

        labelfont = ImageFont.truetype(options['font'], options['labelsize'])

        # This is broken in older pillow versions, using fix from https://github.com/python-pillow/Pillow/commit/60628c77b356d0617932887453c3783307aa682a
        ##(fw,fh) = font.getsize(text)
        fsize, foffset = labelfont.font.getsize(text)
        (fw, fh) = (fsize[0] + foffset[0], fsize[1] + foffset[1])
        # Still not working right, do some tweaking
        labelfontheight = labelfont.font.ascent + labelfont.font.descent

    (ts, dum) = labelfont.font.getsize(text)

    while ts[0] > size[0] and len(text) > 3:
        text = "..." + text[4:]
        (ts, dum) = labelfont.font.getsize(text)

    x = (size[0] - ts[0]) / 2 + pos[0]
    y = pos[1] + size[1] - labelfontheight

    draw.rectangle(((x-2, y-2),(x + ts[0] + 4, y + ts[1] + 2)), fill=(0,0,0,64))
    draw.text((x,y), text, font=labelfont, fill=options['labelcolor'])



# Create a thumbnail page of size width x height using as many images from imgs as possible while keeping their height at least at 75% 
# and at most 125% of thimgsize
# forceFullSize: create a layout of exactly the given size, otherwise it could be smaller
# crop: if the images are too big for the size, allow horizontally cropping them
# background: background color
# topoffset: space to leave empty (for headers) at the top
# border: size of border around each image
# cover: image to use for cover (top-left corner)
# if height == -1 determine it automatically
# NOTE: imgs is changed! broken imges are removed and filenames may be replaced by actual images!

def layoutImages(width, height, imgs, thimgsize = 150, forceFullSize = True, crop = False, background = (255,255,255), topoffset = 0, border = 0, cover = None, loptions = None, labels = False, progress = None, zip = None):
    
    if len(imgs) == 0:
        raise UserWarning("layoutImages: got no images to layout?!?\n")
    
    log(LogLevels.DEBUG, "layoutImages: width:%d height:%d\n" % (width, height))
    log(LogLevels.DEBUG, "layoutImages: imgs:%s\n" % (imgs))

    start = time.time()

    maxw = maxh = -1

    # Special case: 1x1 thumbnail
    if width == thimgsize and height == thimgsize:
        i = 0
        while i < len(imgs):
            if not isinstance(imgs[i], Image.Image):
                try:
                    if zip is None:
                        im = Image.open(StringIO(zip.read(imgs[i])))
                    else:
                        im = Image.open(imgs[i])

                    imgs[i], factor = preresize(im, (thimgsize,thimgsize))

                    # Was this image loaded? If not, load it to test integrity
                    if factor == 1:
                        imgs[i].load()

                except IOError:
                    del imgs[i]
                    continue
            
            if crop == False:
                log(LogLevels.DEBUG, "layoutImages: resized to (%d,%d)\n" % (width, height))
                imgs[i] = resize(imgs[i], (width, height))
                return imgs[i], imgs[i].size[0], imgs[i].size[2] 
            else:
                
                scale = height / float(imgs[i].size[1])
                w = int(imgs[i].size[0] * scale)

                im = imgs[i].resize((w, thimgsize), Image.LINEAR)

                imgs[i] = im.crop((0, 0, thimgsize, thimgsize))
                
                log(LogLevels.DEBUG, "layoutImages: cropped to (%d,%d)\n" % (thimgsize, thimgsize))
                
                return imgs[i], imgs[i].size[0], imgs[i].size[2]

            raise UserWarning("layoutImages: none of the images are readable (%s)!\n" % imgs)
    
    
    # Get image sizes and check images for correctness
        
    nimgs = len(imgs)
    
    if nimgs == 0:
        raise UserWarning("layoutImages: No images to layout? (%s)!\n" % imgs)  
    
    # Step 1: Fill rows of images until height is reached or images are exhausted
    rows = []
    rowfactors = []
    rowwidths = []
    rowheights = []
    tsizes = []

    h = topoffset + border

    if cover and width - cover.size[0] < thimgsize:

        h = topoffset + 2 * border + cover.size[1]
        coverset = True
    else:
        coverset = not cover

    curimg = 0
    coverrows = 0

    while (h < height or height == -1) and curimg < nimgs:

        # Try to keep space for cover, if any
        rowwidth = width
        if not coverset:
            cs = cover.size

            if h < cs[1]:

                rowwidth = width - cs[0] - border

            else:
                # Adjust height of rows next to cover and cover to match
                tw = width - cs[0] - border
                th = h - topoffset - 2 * border
                log(LogLevels.DEBUG, "cs=%s tw=%d th=%d topoffset=%d\n" % (cs, tw, th, topoffset))

                cfactor = float(tw + cs[0])/(cs[0] + float(cs[1]) / th * tw)
                tfactor = cfactor * float(cs[1]) / th

                # New layout for cover-side rows. Start from the top.
                h = topoffset + border

                nrw = int(rowwidths[0] * tfactor)

                for ri, row in enumerate(rows):
                    ts, rh, factor, leftover = layoutRow(row, nrw, border=border, thimgsize=thimgsize)

                    tsizes[ri] = ts
                    rowfactors[ri] = factor
                    rowwidths[ri] = nrw
                    rowheights[ri] = rh

                    h += rh + border

                    log(LogLevels.DEBUG, "rw=%d\n" % rowwidths[ri])

                log(LogLevels.DEBUG, "h=%f tfactor=%f\n" % (h,tfactor))

                # Make cover fit tight
                cb = (width - rowwidths[0] - border, h - topoffset - 2 * border)

                log(LogLevels.DEBUG, "cfactor=%f cs=%s cb=%s\n" % (cfactor, cs,cb))
                cover = resize(cover, cb, center=False)
                log(LogLevels.DEBUG, "cover.size=(%d,%d)\n" % (cover.size))

                coverset = True
                coverrows = len(rows)

        if progress:
            if progress(curimg / float(nimgs), 0.):
                raise AbortException()


        log(LogLevels.DEBUG, "layoutImages: rowwidth=%d\n" % rowwidth)

        # Current row
        lastrow = None
        lastts = None
        lastfactor = 0
        lastrh = 0

        row = []
        ts = []
        rh = 0
        factor = 1000

        # Keep adding pictures until factor gets under 1, then pick closer one
        while factor > 1 and curimg < nimgs:
            lastrow = copy.copy(row)
            lastfactor = factor
            lastts = copy.copy(ts)
            lastrh = rh

            # Is the next image loaded? If not, get it, removing broken images on the way
            # This is more effective than loading all images if only a subset is used
            while curimg < nimgs and not isinstance(imgs[curimg], Image.Image):
                try:

                    log(LogLevels.DEBUG, "layoutImages: loading (%d) %s " % (curimg, imgs[curimg]))
                    log(LogLevels.PROGRESS, ".")

                    if zip is None:
                        imgs[curimg] = Image.open(imgs[curimg])
                    else:
                        ifn = imgs[curimg]
                        imgs[curimg] = Image.open(StringIO(zip.read(imgs[curimg])))
                        imgs[curimg].filename = ifn

                    maxw = max(maxw, imgs[curimg].size[0])
                    maxh = max(maxh, imgs[curimg].size[1])

                    imgs[curimg], ifac = preresize(imgs[curimg], (thimgsize, thimgsize))

                    log(LogLevels.DEBUG, "(%dx%d)\n" % (imgs[curimg].size[0], imgs[curimg].size[1]))

                    # Was this image loaded by preresize? If not, load it to test integrity
                    if ifac == 1:
                        imgs[curimg].load()

                    break
                except Exception:
                    del imgs[curimg]
                    nimgs -= 1

            row.append(imgs[curimg])
            curimg += 1

            ts, rh, factor, leftover = layoutRow(row, rowwidth, border=border, thimgsize=thimgsize)

        if abs(factor - 1) < abs(lastfactor - 1):
            tsizes.append(ts)
            rows.append(row)
            rowfactors.append(factor)
        else:
            tsizes.append(lastts)
            rows.append(lastrow)
            rowfactors.append(lastfactor)
            rh = lastrh
            curimg -= 1

        rowwidths.append(rowwidth)
        rowheights.append(rh)

        h += rh + border

    # Do we need to adjust last row? Can happen if only a few images in it.
    if rowfactors[-1] > 1.25 and len(rows) > 2:
        # Try to borrow an image from row with smallest scale

        si = -1
        ss = 100
        facsum = 0
        for i in range(coverrows, len(rows)):
            facsum += rowfactors[i]
            if rowfactors[i] <= ss:
                ss = rowfactors[i]
                si = i

        if si != -1:
            pass



        slr = rows[-2][:-1]
        lr = rows[-2][-1:] + rows[-1]

        sts, srh, sfactor, sleftover = layoutRow(slr, rowwidths[-2], border=border, thimgsize=thimgsize)
        lts, lrh, lfactor, lleftover = layoutRow(lr, rowwidths[-1], border=border, thimgsize=thimgsize)

        if sfactor + lfactor < rowfactors[-2] + rowfactors[-1]:
            rows[-2:]       = [slr, lr]
            rowfactors[-2:] = [sfactor, lfactor]
            tsizes[-2:]     = [sts, lts]

            h = h - rowheights[-2] - rowheights[-1] + srh + lrh


    log(LogLevels.PROGRESS, "\nAssembling result: ")

    if height == -1:
        height = h

    if h > height:
    # Remove last row, don't want partial images
        log(LogLevels.DEBUG, "layoutImages: height %d too big, removing last row.\n" % (h))
        h -= tsizes[-1][0][1] + border
        rows = rows[:-1]
        rowwidths = rowwidths[:-1]
        rowfactors = rowfactors[:-1]
        tsizes = tsizes[:-1]

    log(LogLevels.DEBUG, "layoutImages: rows: %s rowwidths: %s\n" % (rows, rowwidths))

    # Step 3: Assemble images
    if forceFullSize == False:
        height = h
        width = max(rowwidths)

    out = Image.new("RGB", (width, height), background)
    y = int(math.floor((height - h) / 2)) + topoffset + border
    draw = ImageDraw.Draw(out, "RGBA")

    if cover:
        out.paste(cover, (border, y))

        if labels:
            lt = cover.filename.rsplit(os.path.sep, 1)[-1]

            drawLabel(out, draw, lt, (border, y), cover.size, loptions)

        if width - cover.size[0] <= thimgsize:
            y = topoffset + 2 * border + cover.size[1]

    ic = 0
    for i in xrange(0, len(rows)):
        r = rows[i]
        rw = rowwidths[i]
        if cover and y < cover.size[1]:
            x = (width-rw) + border
        else:
            x = int((width-rw) / 2.) + border

        for ii,im in enumerate(r):
            t = tsizes[i][ii]
            log(LogLevels.DEBUG, "Out %d (%d,%d) rescaled to %dx%d at %d,%d\n" % (i, im.size[0], im.size[1], t[0] - 2 * border, t[1] - 2 * border, x, y))
            ri = resize(im, (t[0], t[1]), center=False)
            out.paste(ri, (x, y))

            if labels:
                lt = im.filename.rsplit(os.path.sep, 1)[-1]

                drawLabel(out, draw, lt, (x,y), (t[0], t[1]), loptions)

            x += t[0] + border
            log(LogLevels.PROGRESS, ".")
            ic += 1

            if progress:
                if progress(1.0, ic / float(curimg)):
                    raise Exception()

        y += tsizes[i][0][1] + border

    end = time.time()

    log(LogLevels.INFO, " done (took %.2f secs).\n" % (end-start))

    if progress:
            progress(1.0, 1.0)

    return out, maxw, maxh


def createContactSheet(options, folder, progress = None):

    zip = None

    outname = options['output']

    if outname == "auto":
        try:
            fbase, fname = folder.rsplit('/', 1)
        except ValueError:
            fbase = "."
            fname = folder

        if options['outdir'] == "auto" or options['outdir'] == '':
            outbase = fbase
        else:
            outbase = options['outdir']

        if options["zips"] and (folder.endswith("zip") or folder.endswith("ZIP")):
            fname = fname[:-4]

        if len(outbase) > 0 and outbase[-1] == os.path.sep:
            outbase = outbase[:-1]

        outname = outbase + "/" + fname + "." + options['outputtype']

    if options['nooverwrite'] and os.path.isfile(outname):
        log(LogLevels.INFO, "%s already exists, not overwriting.\n" % outname)
        return

    fre = re.compile(options['filetype'])

    if os.path.isfile(folder) and zipfile.is_zipfile(folder):
        zip = zipfile.ZipFile(folder)

        files = []
        for f in zip.infolist():
            if fre.match(f.filename):
                files.append(f.filename)

    elif not options['recursive']:
        files = os.listdir(folder)
        files = [ os.path.join(folder,f) for f in files if fre.match(f) ]
    else:
        files = []
        for root, dirs, dfiles in os.walk(folder):
            files += [os.path.join(root, f) for f in dfiles if fre.match(f) ]


    if len(files) == 0:
        log(LogLevels.ERROR, "Found no images to process for folder %s, skipping!\n" % folder)
        return

    if options['random']:
        for i in xrange(0, len(files)):
            dest = random.randrange(len(files))
            f = files[dest]
            files[dest] = files[i]
            files[i] = f
    else:
        files.sort()


    try:
        f = folder.rsplit('/', 1)[-1]
    except IndexError:
        f = folder

    log(LogLevels.INFO, "%s: %d images..." % (f, len(files)))


    if options['cover'] != "none":

        cov = options['cover']
        if options['cover'] == "auto":
            cov = "^.*(cover(?!-clean)|index).*"

        covre = re.compile(cov)

        cands = []
        for f in files:
            if covre.match(f):
                cands.append(f)

        if len(cands) == 0:
            log(LogLevels.DEBUG, "Found no cover candidate, using first image.\n")
            cands.append(files[0])

        elif len(cands) > 1:
            log(LogLevels.DEBUG, "Found more than 1 cover candidate (%s), using first, ignoring others.\n" % cands)

        # Remove cover(s) from files list
        files = [ f for f in files if not f in cands ]

        log(LogLevels.DEBUG, "Loading and scaling cover %s...\n" % cands[0])

        # Load and scale cover image
        if not zip is None:
            cover = Image.open(StringIO(zip.read(cands[0])))
            cover.filename = cands[0]
        else:
            cover = Image.open(cands[0])

        if options['coverscale'] > 0:
            factor = options['thumbheight'] * options['coverscale'] / float(cover.size[1])
            if cover.size[0] * factor > options['thumbheight'] * options['coverscale']:
                factor = options['thumbheight'] * options['coverscale'] / float(cover.size[0])
            csize = (int(cover.size[0] * factor), int(cover.size[1] * factor))
        else:
            cw = options['width'] - 2.0 * options['border']
            factor = cw / cover.size[0]
            csize = (int(cover.size[0] * factor), int(cover.size[1] * factor))

        cover = resize(cover, csize, center=False)
    else:
        cover = None


    if options['title'] == "none":
        sheet, maxw, maxh = layoutImages(options['width'], options['height'], files, cover=cover, thimgsize = options['thumbheight'], background = options['background'], border = options['border'], forceFullSize = False, labels = options['labels'], loptions = options, progress=progress, zip=zip)
    else:

        if not os.path.isfile(options['font']):
            options['font'] = os.path.join(basedir, options['font'])

        font = ImageFont.truetype(options['font'], options['fontsize'])

        # This is broken in older pillow versions, using fix from https://github.com/python-pillow/Pillow/commit/60628c77b356d0617932887453c3783307aa682a
        ##(fw,fh) = font.getsize(options['title'])
        size, offset = font.font.getsize(options['title'])
        (fw, fh) = (size[0] + offset[0], size[1] + offset[1])
        # Still not working right, do some tweaking
        fh = font.font.ascent + font.font.descent

        fh += 2 # Add a little border

        sheet, maxw, maxh = layoutImages(options['width'], options['height'], files, cover=cover, thimgsize = options['thumbheight'], background = options['background'], topoffset = fh, border = options['border'], forceFullSize = False, labels = options['labels'], loptions = options, progress=progress, zip=zip)

        draw = ImageDraw.Draw(sheet)

        t = options['title']
        if t == "auto":
            t = folder
            if t[-1] == '/':
                t = t[:-2]
            t = t.rsplit('/', 1)[-1]

        if options['tstats']:
            n = 0

            for f in files:
                if isinstance(f,Image.Image):
                    n += 1

            if maxw == maxh:
                t += " (x%d) max %d pix" % (n, maxw)
            else:
                t += " (x%d) max %dx%d" % (n, maxw, maxh)

        (fw,fh) = font.getsize(t)

        draw.text(( (options['width'] - fw) / 2,0), t, font=font, fill=options['titlecolor'])


    log(LogLevels.PROGRESS, "Writing contact sheet to %s.\n" % outname)
    sheet.save(outname, quality=options['quality'])



def processFolder(options, folder, progress = None):

    if folder[-1] == os.path.sep:
        folder = folder[:-1]

    fre = re.compile(options['filetype'])

    # Zip file?
    if os.path.isfile(folder) and zipfile.is_zipfile(folder):
        zip = zipfile.ZipFile(folder)

        nf = 0
        for f in zip.infolist():
            if fre.match(f.filename):
                nf += 1

        if nf > 0:
            createContactSheet(options, folder, progress)

        return

    # Directory?
    if not os.path.isdir(folder):
        log(LogLevels.INFO, "%s is not a folder, skipped.\n" % folder)
        return

    if options["subdircontacts"] == False:
        createContactSheet(options, folder, progress)
    else:
        for r in os.walk(folder):

            f = r[0].replace(os.path.sep, '/')

            # Any images in this folder?
            files = [ ff for ff in os.listdir(f) if fre.match(ff) ]

            ##print r,f,files
            
            if len(files) > 0:
                createContactSheet(options, f, progress)

            # Any zips in this folder?
            if options["zips"]:
                for ff in os.listdir(f):
                    fff = os.path.join(f,ff)
                    if zipfile.is_zipfile(fff):
                        createContactSheet(options, fff, progress)
                
                


if __name__ == "__main__":

    # Main program

    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)

    parser = argparse.ArgumentParser("Create contact sheet(s) for image folders")

    parser.add_argument("-l", "--loglevel",       dest="loglevel",       default=LogLevels.PROGRESS, type=int, help="log level (1-5)")
    parser.add_argument("-o", "--output",         dest="output",         default="auto",         help="output filename, or auto")
    parser.add_argument(      "--outputtype",     dest="outputtype",     default="jpg",          help="output filetype for auto output")
    parser.add_argument(      "--outdir",         dest="outdir",         default="auto",         help="output firectory for contact sheets, or auto")
    parser.add_argument(      "--quality",        dest="quality",        default=85,             type=int, help="output JPEG quality")
    parser.add_argument(      "--thumbheight",    dest="thumbheight",    default=200,            type=int, help="height of thumbnails")
    parser.add_argument(      "--width",          dest="width",          default=900,            type=int, help="width of contact sheet")
    parser.add_argument(      "--height",         dest="height",         default=-1,             type=int, help="height of contact sheet (-1: auto-detect)")
    parser.add_argument("-b", "--background",     dest="background",     default="#000000",      help="background color")
    parser.add_argument(      "--filetype",       dest="filetype",       default=".*\.(jpg|jpeg|JPG|JPEG)$",        help="regex expression to pick files to use")
    parser.add_argument("-t", "--title",          dest="title",          default="auto",         help="title to add to top of sheet, auto for default, none for none")
    parser.add_argument(      "--tstats",         dest="tstats",         default=False,          action="store_true", help="add statistics after title")
    parser.add_argument(      "--titlecolor",     dest="titlecolor",     default="#ffffff",      help="color of title text")
    parser.add_argument(      "--border",         dest="border",         default="0",            type=int, help="width of border around thumbnails")
    parser.add_argument(      "--coverscale",     dest="coverscale",     default=3.0,            type=float, help="scale factor for cover size")
    parser.add_argument("-c", "--cover",          dest="cover",          default="none",         help="cover image filename regex, picked from images, auto for default")
    parser.add_argument(      "--font",           dest="font",           default="FreeSans.ttf", help="font file to use for title")
    parser.add_argument(      "--fontsize",       dest="fontsize",       default=24,             type=int, help="size of title text")
    parser.add_argument(      "--random",         dest="random",         default=False,          action="store_true", help="randomize order of images")
    parser.add_argument("-r", "--recursive",      dest="recursive",      default=False,          action="store_true", help="recursive collect images from subfolders")
    parser.add_argument(      "--zips",           dest="zips",           default=False,          action="store_true", help="try to use zip files as image sources")
    parser.add_argument(      "--subdircontacts", dest="subdircontacts", default=False,          action="store_true", help="recursively create contact sheets for subfolders")
    parser.add_argument(      "--no-overwrite",   dest="nooverwrite",    default=False,          action="store_true", help="don't overwrite existing contact sheets")
    parser.add_argument(      "--labels",         dest="labels",         default=False,          action="store_true", help="put labels at bottom of thumbnails")
    parser.add_argument(      "--labelsize",      dest="labelsize",      default="8",            type=int, help="font size for labels")
    parser.add_argument(      "--labelcolor",     dest="labelcolor",     default="#ffffff",      help="color for labels")
    parser.add_argument(      "--gui",            dest="gui",            default=False,          action="store_true", help="run GUI")
    parser.add_argument(      "--options",        dest="options",        default=None,           help="load options from file, overwriting command-line options")

    parser.add_argument('folders', nargs='*', metavar='folders', type=str,  help='folders/zipfiles to create contacts for')
    
    options = parser.parse_args()


    if not options.options is None:
        fh = open(options.options, "r")
        opt = json.load(fh)
        fh.close()
        opt["gui"] = options.gui
        options = opt
    else:
        options = vars(options) # Turn into dict for easier load/save

    logLevel = options['loglevel']

    if "-gui" in sys.argv[0]:
        options["gui"] = True

    if options['gui']:
        
        import make_contact_gui
       
        make_contact_gui.run(options, args)
        
        sys.exit(0)
        
   
    if len(options["folders"]) == 0:
        parser.print_help()
        sys.exit(1)

    
    for folder in options["folders"]:
        processFolder(options, folder)
