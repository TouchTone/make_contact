# make_contact

This was found on the web at http://pastebin.com/UYzmT5X9, and assumed to be
Open Source. I fixed some problems and added some features, main credit to the
original uploader. 

## Instruction for Windows users

Download the latest relese from
https://github.com/TouchTone/make_contact/releases, put it in the folder where
you want to install it and execute the program there (or extract it using 7z to the place
you want it to go to).

To use it just drop the folder you want to create the contact sheet for onto
the make_contact.bat script. You can do this with multiple folders, they will be
created one after the other.

If you want to customize the options (like contact sheet sizes etc.), edit the
make_contact.bat file, it has a set of variables at the top that should be
fairly self-explanatory after reading the rest of this document. If not, just
open a ticket here and ask.

You can also register the program as a shell extension. To do that run the
register.bat script. Once that is done you can right-click on a folder and use
the Contact Sheet option.

## Instruction for Windows users

Download the latest relese from
https://github.com/TouchTone/make_contact/releases, put it in the folder where
you want to install it and execute the program there (or extract it using 7z to the place
you want it to go to).

It has a GUI now, just run the make_contact_gui.bat batch file to start it. Set your desired 
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

You might want to make then contact sheet wider, if you have a large monitor.
You can control that with the --width option.

`make_contact.py --width=1600 <folderwithpictures>`


You might want to change the size of the thumbnails, to keep the size of the
contact sheet a little smaller, or to show more details in you need them. The
"--thumbheight" (or just "-t") does that (especially useful for large folders)

`make_contact.py --width=1600 -t 100 <folderwithpictures>`


For folders with a LOT of pictures the contact sheet can get very, very large,
easily larger than your memory can handle. To control the size of the
contact sheet you can define a maximum height using the "--height" option. By
default (or if set to -1) it will automatically expand to the needed size. If set
to another value it will stop once it cannot fit any more images. The result
can be a little smaller than the maximum, to avoid half images or empty space.

`make_contact.py  --width 1280 -t 100 --height 1024 <folderwithpictures>`


Sometimes it can be hard to see where one image ends and the next begins. To
make that more obvious you can add a border around the images using the
"--border" option.

`make_contact.py  -t 100 --height 1024 --border 2 <folderwithpictures>`


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
There is not really a TTF font that
is installed on EVERY system. You can pick any TTF font of your choice and
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


The thumbnails don't always make it easy to get a good idea of the types of
images in the folder. To show one image in more detail it is possible to define
a cover image that is display larger, using the "--cover" option. If set to
"auto" it looks for images called "*cover*" or "*index*", if it doesn't find any
it uses the first image. It can also be used to explicitly pick the image to use
for the cover. The parameter is a regular expression, to allow picking different
images from each processed folder. The example picks the file called "013.jpg"
from each folder, if it exists, if not it just uses the first image.

`make_contact.py --height 1024  --title auto --tstats --cover ".*/013.jpg" <folder> <folder2>`


This covers the main options. Run "make_contact.py -h" for a complete list, it
should be (hopefully) self-explantory.

