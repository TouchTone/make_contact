# make_contact

This was found on the web at http://pastebin.com/UYzmT5X9, and assumed to be
Open Source. I fixed some problems and added some features, main credit to the
original uploader. 

## Instruction for Windows users

Download the latest release from
https://github.com/TouchTone/make_contact/releases, put it in the folder where
you want to install it and execute the program there (or extract it using 7z to the place
you want it to go to).

It has a GUI now, just run make_contact-gui to start it (ot run make_contact --gui). Set your desired
options, select/drag'n'drop the folders, press Run and enjoy.

To use it without GUI just drop the folder(s) you want to create the contact sheet for onto
the make_contact.bat script. You can do this with multiple folders, they will be
created one after the other.

If you want to customize the options (like contact sheet sizes etc.), edit the
make_contact.bat file, it has a set of variables at the top that should be
fairly self-explanatory after reading the rest of this document. If not, just
open a ticket here and ask.

You can also register the program as a shell extension. To do that run the
register.bat script. Once that is done you can right-click on a folder and use
the Contact Sheet option. If you do that with multiple folders it will start a separate 
instance of the program for each, eating up a lot of memory. If you want to do multiple
folders drag them onto the make_contact.bat or use the GUI.

Most of the options should be pretty self-explanatory (ask if you have questions).
See below for an explanation of the different options. especially the --recurse, --subdirimages
and --zips options probably need an explanation.


## Instructions on how to use the make_contact.py script directly

make_contact.py tries to make a nice-looking contact sheet for a folder full of
images. To do that it loads all of them and arranges them in scaled down
versions in a regular pattern. It understands a variety of options to control
the result, you can get a quick overview by calling "make_contact.py -h". Some
more detailed examples foloow.

Trivial usage: `make_contact.py <folderwithpictures>`

This will use all the default arguments and create a file called
<folderwithpictures>.jpg. Pick a folder with pictures that you like and try it
(pick one with less than 100 pictures to keep the run time fast for testing ;).
Open an image viewer for the contact.jpg and just keep it open. Pretty, no? So,
what else do you need?

If you have your images in a .zip archive you don't have to unpack them, just specify the archive name
instead of a folder:

`make_contact.py <zip file>`

If you want to skip all the manual command-line options as described below you can run the system in GUI mode 
by using the "--gui" option. You might still want to read the rest of this README to better understand the options.

`make_contact.py --gui`


You might want to make then contact sheet wider, if you have a large monitor.
You can control that with the --width option.

`make_contact.py --width=1600 <folderwithpictures>`


You might want to change the size of the thumbnails, to keep the size of the
contact sheet a little smaller, or to show more details in you need them. The
"--thumbheight" (or just "-t") does that (especially useful for large folders)

`make_contact.py --width 1600 --thumbheight 100 <folderwithpictures>`


For folders with a LOT of pictures the contact sheet can get very, very large,
easily larger than your memory can handle. To control the size of the
contact sheet you can define a maximum height using the "--height" option. By
default (or if set to -1) it will automatically expand to the needed size. If set
to another value it will stop once it cannot fit any more images. The result
can be a little smaller than the maximum, to avoid half images or empty space.

`make_contact.py  --width 1280 --thumbheight 100 --height 1024 <folderwithpictures>`


Sometimes it can be hard to see where one image ends and the next begins. To
make that more obvious you can add a border around the images using the
"--border" option.

`make_contact.py  --thumbheight 100 --height 1024 --border 2 <folderwithpictures>`


If you have many folders with images, you can add a title at the top so you know
which contact belongs to which folder. The "--title" options does that:

`make_contact.py  --height 1024 --title "Folder 1" <folder>`

WARNING: You might encounter an error message like the following

Traceback (most recent call last):
  File "make_contact.py", line 504, in <module>
    font = ImageFont.truetype(options.font, options.fontsize)
  File "/usr/lib64/python2.7/site-packages/PIL/ImageFont.py", line 218, in truetype
    return FreeTypeFont(filename, size, index, encoding)
  File "/usr/lib64/python2.7/site-packages/PIL/ImageFont.py", line 134, in __init__
    self.font = core.getfont(file, size, index, encoding)
IOError: cannot open resource

By default the script uses the font "FreeSans.ttf" from the directory where the script is. 
You can pick any TTF font of your choice and
specify it with the "--font" option. It's easy to find lots of free TTF fonts on
the web.


The system can handle generating multiple contact sheets in one call, just pass
multiple folders to it. For that to make sense with titles you can set the title
to "auto", which will use the last component of the folder path as the title.

`make_contact.py --height 1024 --title auto <folder> <folder2> <folder3>`


Sometimes you might be interested in some basic statistics of the images in the
folder, especially when you limit the size and skip some images. Using the
"--tstats" option adds the number and maximum size of images to the title.

`make_contact.py --height 1024 --title auto --tstats <folder>`


If you don't like the white on black text you can customize it using the
"--background" (or "-b"), "--titlecolor" and "--fontsize" options. The first two
understand Python ImageColor colorspecs (see
http://effbot.org/imagingbook/imagecolor.htm for details).

`make_contact.py --height 1024 --title auto --titlecolor="#ffff00" --background="rgb(0,0,255)" --fontsize 36  <folder>`


In some cases it can be useful to know the filenames for all the displayed images. The "--labels" options
 will add a small label with the filename at the bottom of the thumbnail.
 
`make_contact.py --height 1024 --title auto --labels <folder>`

You can use the "--labelsize" and "--labelcolor" options to adjust the labels as needed.


The thumbnails don't always make it easy to get a good idea of the types of
images in the folder. To show one image in more detail it is possible to define
a cover image that is displayed larger, using the "--cover" option. If set to
"auto" it looks for images called "*cover*" or "*index*", if it doesn't find any
it uses the first image. It can also be used to explicitly pick the image to use
for the cover. The parameter is a regular expression, to allow picking different
images from each processed folder. The example picks the file called "013.jpg"
from each folder, if it exists, if not it just uses the first image. In most cases "auto" should be fine.

`make_contact.py --height 1024  --title auto --tstats --cover ".*/013.jpg" <folder> <folder2>`

You can also control the size of the cover image using the "--coverscale" option. It is given in the number of 
thumbnails images that should fit next to it, the default is 3, which might not be enough for small thumbnails. 
If set to 0 the cover will fill the full width of the contact sheet.

`make_contact.py --thumbheight 75 --title auto --tstats --cover auto --coverscale 4 <folder> <folder2>`


Sometimes you don't want the contact sheet in the parent folder of the image folder. They can be redirected to a 
different folder using the "--outdir" option. 

`make_contact.py  --title auto --tstats --cover auto --outdir contacts <folder> <folder2> <folder3> <folder4>`

If you have a lot of folders having to specify each one of them can be painful. To simplify the process of creating 
sheets for many folders you can use the "--subdircontacts" option. It will automatically create contact sheets for all 
_subdirectories_ of the folders you specify (not for the actual folders). 
In the GUI this option is called "Create contacts for subdirs". 

`make_contact.py  --title auto --tstats --cover auto --outdir contacts --subdircontacts <folder with folders>`

By default this option will ignore zip archives. To 
include those too use the "--zips" option ("Use .zip as image sources" in the GUI).

If you do this for a lot of folders it can take a long time. In cases where some of the subdirs are unchanged it would 
recreate the contact sheets, even though they are unchanged. To avoid that it is possible to only create contact sheets 
for folders that don't have any yet, using the "--no-overwrite" option.

Depending on the organization of your folders it can also be useful to not create a separate contact sheet for each 
folder, but to combine the images from all subfolders into one contact sheet. This can be done using the "--recursive" 
option ("Use images from subdirs" in the GUI).



This covers the main options. Run "make_contact.py -h" for a complete list, it
should be (hopefully) self-explantory.

