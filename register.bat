

reg.exe ADD "HKCR\Folder\shell\Contact Sheet" /f  /d "Contact Sheet"

reg.exe ADD "HKCR\Folder\shell\Contact Sheet\command" /f  /d "\"%~dp0make_contact.bat\" \"%%1\""
