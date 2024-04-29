Cloudooo X2T handler
====================

Table of content :

- Description
- Handled Mimetypes
- Contributors


Description
-----------

The `cloudooo.handler.x2t.handler` is a conversion handler that uses Ascensio
System OnlyOffice x2t converter.

This binary is theoricaly able to convert many document formats including open
documents and microsoft documents, but the x2t handler was designed to handle
from "x" format (i.e. DOCX, PPTX, XLSX) to OnlyOffice format only.

Here, the term "y" format (i.e. DOCY, PPTY, XLSY) defines document format used
by OnlyOffice apps. These "y" formats are just file extensions used by Cloudooo
to send resulting OnlyOffice converted document correctly.

A "y" file can be :

- a raw file containing base64 of body data without any component (metadata,
  images, ...) ;
- or a zip file containing :
    - "body.txt" - a raw file containing base64 of body data without component ;
    - "metadata.json" - a json representation of document metadata ;
    - "media/" - a folder containing document component.


Handled Mimetypes
-----------------

- application/x-asc-text (docy) ;
- application/x-asc-presentation (ppty) ;
- application/x-asc-spreadsheet (xlsy).


Contributors
------------

Based on `cloudooo.handler.yformat.handler` from Boris Kocherov original work.

- Boris Kocherov <bk@raskon.ru>
- Tristan Cavelier <tristan.cavelier@nexedi.com>
