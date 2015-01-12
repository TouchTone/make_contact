#!/usr/bin/python

# Make a contact sheet for a directory containing images.

# This is copy-n-pasted from another system, so apologies for it being a little messy...


import os, sys, glob, re, math, random, fnmatch
from PIL import Image, ImageDraw, ImageFont
from optparse import OptionParser


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

def log(level, msg):
    if logLevel >= LogLevels.DEBUG and level == LogLevels.PROGRESS:
        # Don't let progress mess up debug log
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
    
    return img


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

def layoutImages(width, height, imgs, thimgsize = 150, forceFullSize = True, crop = False, background = (255,255,255), topoffset = 0, border = 0, cover = None):

    ##theCI.stat_nthumbs_created += 1
    
    if len(imgs) == 0:
        raise UserWarning("layoutImages: got no images to layout?!?\n")
    
    log(LogLevels.DEBUG, "layoutImages: width:%d height:%d\n" % (width, height))
    log(LogLevels.DEBUG, "layoutImages: imgs:%s\n" % (imgs))
    
    maxw = maxh = -1
    
    # Special case: 1x1 thumbnail
    if width == thimgsize and height == thimgsize:
        i = 0
        while i < len(imgs):
            if not isinstance(imgs[i], Image.Image):
                try:
                    im = Image.open(imgs[i])

                    imgs[i], factor = preresize(im, (thimgsize,thimgsize))

                    # Was this image loaded? If not, load it to test integrity
                    if factor == 1:
                        imgs[i].load()
                    
                    ##theCI.stat_nimages_loaded += 1
                    ##theCI.stat_npixels_loaded += imgs[i].size[0]*imgs[i].size[1]
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
    rowwidths = []
    tsizes = [] # Target sizes for images
    h = topoffset + border

    curimg = 0
    rowfirstimg = 0
    
    log(LogLevels.PROGRESS, "Reading and layouting images: ")
    
    coverset = not cover

    while (h < height or height == -1) and curimg < nimgs:
        # Fill row with images
        row = []
        w = 0
        rowfirstimg = curimg
        
        log(LogLevels.DEBUG, "layoutImages: start row\n")
         
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
                
                cfactor = float(tw + cs[0])/(cs[0] + float(cs[1]) / th * tw  ) 
                tfactor = cfactor * float(cs[1]) / th
                
                for r in xrange(0, len(rows)):
                    rowwidths[r] = int(rowwidths[r] * tfactor)
                    rw = 0
                    for i in rows[r]:
                        log(LogLevels.DEBUG, "pre-scale: ts[%d]=%s\n" % (i, tsizes[i]))
                        tsizes[i] = (int(tsizes[i][0] * tfactor), int(tsizes[i][1] * tfactor))
                        rw += tsizes[i][0] + border
                        log(LogLevels.DEBUG, "ts[%d]=%s\n" % (i, tsizes[i]))

                    todo = rowwidths[r] - rw
                    ind = rows[r][0]
                    while todo:
                        tsizes[ind] = (tsizes[ind][0] + 1, tsizes[ind][1])
                        todo = todo - 1
                        ind = ind + 1
                        if ind >= curimg:
                            ind = rowfirstimg

                    log(LogLevels.DEBUG, "rw=%d\n" % rowwidths[r])
 
                # Adjust to new thumbs' height
                h = int(h * tfactor)
                log(LogLevels.DEBUG, "h=%f tfactor=%f\n" % (h,tfactor))
               
                # Make cover fit tight
                cb = (width - rowwidths[0] - border, h - topoffset - 2 * border)
                
                log(LogLevels.DEBUG, "cfactor=%f cs=%s cb=%s\n" % (cfactor, cs,cb))
                cover = resize(cover, cb, center=False)  
                log(LogLevels.DEBUG, "cover.size=(%d,%d)\n" % (cover.size))

                coverset = True

        log(LogLevels.DEBUG, "layoutImages: rowwidth=%d\n" % rowwidth)

        while w < rowwidth and curimg < nimgs:
        
            # Is the next image loaded? If not, get it, removing broken images on the way
            # This is more effective than loading all images if only a subset is used
            while curimg < nimgs and not isinstance(imgs[curimg], Image.Image):
                try:
                    
                    log(LogLevels.DEBUG, "layoutImages: loading (%d) %s " % (curimg, imgs[curimg]))
                    log(LogLevels.PROGRESS, ".")
                    
                    imgs[curimg] = Image.open(imgs[curimg])
  
                    maxw = max(maxw, imgs[curimg].size[0])
                    maxh = max(maxh, imgs[curimg].size[1])

                    imgs[curimg], factor = preresize(imgs[curimg], (thimgsize, thimgsize))
                    
                    log(LogLevels.DEBUG, "(%dx%d)\n" % (imgs[curimg].size[0], imgs[curimg].size[1]))

                    # Was this image loaded? If not, load it to test integrity
                    if factor == 1:
                        imgs[curimg].load()
                  
                    ##theCI.stat_nimages_loaded += 1
                    ##theCI.stat_npixels_loaded += imgs[curimg].size[0]*imgs[curimg].size[1]
                    break
                except Exception:
                    del imgs[curimg]
                    nimgs -= 1
                        
            if curimg >= nimgs:
                break
            
            im = imgs[curimg]
            
            # Scale factor to thumbnail size
            factor = thimgsize / float(im.size[1])
            if im.size[0] * factor > rowwidth:
                factor = rowwidth / float(im.size[0])
                    
            log(LogLevels.DEBUG, "layoutImages: scale factor (%d): %f => (%dx%d)\n" % (curimg, factor, int(im.size[0] * factor), int(im.size[1] * factor)))
                
            tsizes.append((int((im.size[0]) * factor), int((im.size[1]) * factor)))
        
            w += tsizes[curimg][0]
            row.append(curimg)
            curimg += 1
     
        if nimgs == 0:
            raise UserWarning("layoutImages: none of the images are readable (%s)!\n" % imgs) 
    
        if w == 0:
            raise UserWarning("layoutImages: layout width = 0!\n") 

        factor = (rowwidth - (len(row) + 1) * border) / float(w)
        
        log(LogLevels.DEBUG, "layoutImages: pre-adjust finish row. width=%d factor=%f height=%d h=%d tsizes=%s\n"% (w, factor, tsizes[rowfirstimg][1], h, tsizes[rowfirstimg:]))
       
        # Too wide? Remove last one.
        if factor < 0.75 and len(row) > 1:
            curimg -= 1
            w -= tsizes[curimg][0]
            tsizes.pop()
            row = row[:-1]
            factor = min((rowwidth - (len(row) + 1) * border) / float(w), 1.25)   
            log(LogLevels.DEBUG, "layoutImages: row too wide, adjusting. new factor=%f\n" % factor)  
        
        # Row too narrow? Scale up (up to 200%)
        if factor > 2:
            factor = 2
        
        # Adjust sizes to make row fit width
        rw = border
        for i in xrange(rowfirstimg, curimg):
            tsizes[i] = (int(tsizes[i][0] * factor), int(tsizes[i][1] * factor))
            rw += tsizes[i][0] + border

        # Second round of adjustments for pixel-accurate results (messes with aspect ratio a little bit)
        todo = rowwidth - rw
        ind = rowfirstimg
        while todo:
            tsizes[ind] = (tsizes[ind][0] + 1, tsizes[ind][1])
            todo = todo - 1
            ind = ind + 1
            if ind >= curimg:
                ind = rowfirstimg

        rw = rowwidth

        rows.append(row)
        rowwidths.append(rw)
        h += tsizes[rowfirstimg][1] + border
        
        log(LogLevels.DEBUG, "layoutImages: finish row. width=%d height=%d h=%d tsizes=%s\n"% (rw, tsizes[rowfirstimg][1], h, tsizes[rowfirstimg:]))

        #if curimg >= nimgs:
        #    break                
    
    log(LogLevels.PROGRESS, "\nAssembling result: ")

    if height == -1:
        height = h + border

    if h > height:
    # Remove last row, don't want partial images
        log(LogLevels.DEBUG, "layoutImages: height %d too big, removing last row.\n" % (h))
        h -= tsizes[rows[-1][0]][1] + border
        rows = rows[:-1]
        rowwidths = rowwidths[:-1]
    
    log(LogLevels.DEBUG, "layoutImages: rows: %s rowwidths: %s\n" % (rows, rowwidths))
       
    # Remove broken images

    # Step 3: Assemble images
    if forceFullSize == False:
        height = h
        width = 0
        for rw in rowwidths:
            width = max(width, rw)

    out = Image.new("RGB", (width, height), background)
    y = int(math.floor((height - h) / 2)) + topoffset + border
    
    if cover:
        out.paste(cover, (border, y))
        
    for i in xrange(0, len(rows)):
        r = rows[i]
        rw = rowwidths[i]
        if cover and y < cover.size[1]:
            x = (width-rw) + border
        else:
            x = int((width-rw) / 2.) + border
        for i in r:
            log(LogLevels.DEBUG, "Out %d (%d,%d) rescaled to %dx%d at %d,%d\n" % (i, imgs[i].size[0], imgs[i].size[1], tsizes[i][0] - 2 * border, tsizes[i][1] - 2 * border, x, y))
            ri = resize(imgs[i], (tsizes[i][0], tsizes[i][1]), center=False)
            out.paste(ri, (x, y))
            x += tsizes[i][0] + border   
            log(LogLevels.PROGRESS, ".")
            ##theCI.stat_nthumbs_used += 1
            
        y += tsizes[i][1] + border
       
    log(LogLevels.PROGRESS, "\n")
        
    return out, maxw, maxh


if __name__ == "__main__":

    # Main program

    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)

    parser = OptionParser()

    parser.add_option("-l", "--loglevel",       dest="loglevel",    default=LogLevels.PROGRESS, type="int", help="log level (1-5)")
    parser.add_option("-o", "--output",         dest="output",      default="auto",         help="output filename, or auto")
    parser.add_option(      "--quality",        dest="quality",     default=85,             type="int", help="output JPEG quality")
    parser.add_option(      "--thumbheight",    dest="thumbheight", default=150,            type="int", help="height of thumbnails")
    parser.add_option(      "--width",          dest="width",       default=1400,           type="int", help="width of contact sheet")
    parser.add_option(      "--height",         dest="height",      default=1100,           type="int", help="height of contact sheet (-1: auto-detect)")
    parser.add_option("-b", "--background",     dest="background",  default="#000000",      help="background color")
    parser.add_option(      "--filetype",       dest="filetype",    default=".*\.(jpg|jpeg|JPG|JPEG)$",        help="regex expression to pick files to use")
    parser.add_option("-t", "--title",          dest="title",       default=None,           help="title to add to top of sheet")
    parser.add_option(      "--tstats",         dest="tstats",      default=False,          action="store_true", help="add statistics after title")
    parser.add_option(      "--titlecolor",     dest="titlecolor",  default="#ffffff",      help="color of title text")
    parser.add_option(      "--border",         dest="border",      default="0",            type="int", help="width of border around thumbnails")
    parser.add_option("-c", "--cover",          dest="cover",       default=None,           help="cover image filename regex, picked from images, auto for default")
    parser.add_option(      "--font",           dest="font",        default="FreeSans.ttf", help="font file to use for title")
    parser.add_option(      "--fontsize",       dest="fontsize",    default=24,             type="int", help="size of title text")
    parser.add_option(      "--random",         dest="random",      default=False,          action="store_true", help="randomize order of images")
    parser.add_option("-r", "--recursive",      dest="recursive",   default=False,          action="store_true", help="recursive collect images from subfolders")

    (options, args) = parser.parse_args()

    logLevel = options.loglevel
    
    for folder in args:
    
        if folder[-1] == os.path.sep:
            folder = folder[:-1]
            
        if not os.path.isdir(folder):
            log(LogLevels.INFO, "%s is not a folder, skipped.\n" % folder)
            continue

        fre = re.compile(options.filetype)            
        
        if not options.recursive:
        
            files = os.listdir(folder)
            files = [ os.path.join(folder,f) for f in files if fre.match(f) ]
            
        else:
        
            files = []
            for root, dirs, dfiles in os.walk(folder):
                files += [os.path.join(root, f) for f in dfiles if fre.match(f) ]
        
        if options.random:
            for i in xrange(0, len(files)):
                dest = random.randrange(len(files))
                f = files[dest]
                files[dest] = files[i]
                files[i] = f
        else:
            files.sort()
 
        if len(files) == 0:
            log(LogLevels.ERROR, "Found no images to process for folder %s, skipping!\n" % folder)
            continue

        log(LogLevels.INFO, "Found %d images to process for folder %s...\n" % (len(files), folder))

        if options.cover:

            cov = options.cover
            if options.cover == "auto":
                cov = ".*(cover|index).*"

            covre = re.compile(cov)

            cands = []       
            for f in files:
                if covre.match(f):
                    cands.append(f)

            if len(cands) == 0:
                log(LogLevels.WARNING, "Found no cover candidate, using first image.\n")
                cands.append(files[0])

            elif len(cands) > 1:
                log(LogLevels.WARNING, "Found more than 1 cover candidate (%s), using first, ignoring others.\n" % cands)        

            # Remove cover(s) from files list
            files = [ f for f in files if not f in cands ]

            log(LogLevels.PROGRESS, "Loading and scaling cover %s...\n" % cands[0])

            # Load and scale cover image
            cover = Image.open(cands[0])

            factor = options.thumbheight * 3 / float(cover.size[1]) 
            if cover.size[0] * factor > options.thumbheight * 3 :
                factor = options.thumbheight * 3 / float(cover.size[0])

            cover = resize(cover, (int(cover.size[0] * factor), int(cover.size[1] * factor)), center=False)        
        else:
            cover = None            


        if options.title == None:
            output, maxw, maxh = layoutImages(options.width, options.height, files, cover=cover, thimgsize = options.thumbheight, background = options.background, border = options.border, forceFullSize = False)
        else:

            if not os.path.isfile(options.font):
                options.font = os.path.join(basedir, options.font)
                
            font = ImageFont.truetype(options.font, options.fontsize)
            (fw,fh) = font.getsize(options.title)

            fh += 2 # Add a little border

            output, maxw, maxh = layoutImages(options.width, options.height, files, cover=cover, thimgsize = options.thumbheight, background = options.background, topoffset = fh, border = options.border, forceFullSize = False)

            draw = ImageDraw.Draw(output)  

            t = options.title
            if t == "auto":
                t = folder
                if t[-1] == os.path.sep:
                    t = t[:-2]
                t = t.rsplit(os.path.sep, 1)[-1]

            if options.tstats:
                n = 0

                for f in files:
                    if isinstance(f,Image.Image):
                        n += 1

                if maxw == maxh:
                    t += " (x%d) max %d pix" % (n, maxw)
                else:
                    t += " (x%d) max %dx%d" % (n, maxw, maxh)

            (fw,fh) = font.getsize(t)    

            draw.text(( (options.width - fw) / 2,0), t, font=font, fill=options.titlecolor)    

        out = options.output
        if out == "auto":
            if folder[-1] == os.path.sep:
                out = folder[:-1] + ".jpg"
            else:
                out = folder + ".jpg"

        log(LogLevels.PROGRESS, "Writing contact sheet to %s.\n" % out)
        output.save(out, "JPEG", quality=options.quality)

