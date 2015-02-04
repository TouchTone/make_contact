ECHO OFF
REM Batch file to set arguments for make_contact


REM These are all the possible arguments, with their default values. 

REM The width of the output sheet 
SET WIDTH=900

REM The height of the output sheet. -1: auto-detect to fit all images
SET HEIGHT=-1

REM The target height of each thumbnail
SET THUMBHEIGHT=200

REM Size of the border between thumbnails
SET BORDER=1

REM Whether to include image resultion statistics in the title
REM Set to empty to disable
SET TSTATS=--tstats

REM Name of the image to use for a cover image. auto: try to pick automatically, none: no cover image
SET COVER=auto

REM Size of the cover image (in number of thumbnail sizes).
SET COVERSCALE=3

REM Don't overwrite existing sheets
REM Set to --no-overwrite to enable
SET NOOVERWRITE=
 
REM The background color
SET BACKGROUND=#000000

REM Title for the sheet. none: no title, auto: use folder name
SET TITLE=auto

REM Font to use for title (TTF file name)
SET FONT=FreeSans.ttf

REM Size of the title font to use
SET FONTSIZE=24

REM Color for the title
SET TITLECOLOR=#ffffff

REM Randomize order of images
REM Set to --random to enable
SET RANDOMIZE=

REM Collect images from sub-directories, too.
REM Set to empty to disable
SET RECURSIVE=--recursive

REM The name of the sheet. auto: folder name + ".jpg"
SET OUTPUT=auto

REM The JPEG compression quality of the sheet (0-100)
SET QUALITY=85
   
REM The level of verbosity (1: very quiet, 5: very noisy)
SET LOGLEVEL=4


SET PROG=%~dp0make_contact.exe

:loop
if "%~1" NEQ "" (
  ECHO ===============================
  ECHO Generating contact sheet for %1
  ECHO -------------------------------
  
  %PROG% --width=%WIDTH% --height=%HEIGHT% --thumbheight=%THUMBHEIGHT% --border=%BORDER% %TSTATS% --cover=%COVER% --coverscale=%COVERSCALE% %NOOVERWRITE% --background=%BACKGROUND% --title=%TITLE% --titlecolor=%TITLECOLOR% --font=%FONT% --fontsize=%FONTSIZE% %RANDOMIZE% %RECURSIVE% --output=%OUTPUT% --quality=%QUALITY% --loglevel=%LOGLEVEL% %1
  
  SHIFT
  goto :loop
)

