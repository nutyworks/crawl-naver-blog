#!/usr/bin/python3

import requests as rq
import bs4 as bs
import json
import re
import os
import uuid
import zipfile
import urllib.request
from shutil import rmtree, make_archive

def flattenChilds(root: bs.element.Tag) -> list:
    ret = []
    for child in root.children:
        if isinstance(child, bs.element.Tag):
            for s in flattenChilds(child):
                ret.append(str(s))
        else:
            ret.append(str(child))

    return ret

baseurl = "https://m.blog.naver.com/%s/%d"
listurl = "https://blog.naver.com/PostTitleListAsync.nhn?blogId=%s&currentPage=%d&categoryNo=%d&countPerPage=30"

blogid = input("Blog ID: ")
categoryno = int(input("Category Number: "))
title = input("Title: ")
creator = input("Creator: ")
cover = input("Cover link: ")

currentpage = 1
lognos = []

while True:  # Until log numbers are fully gathered.
    res = rq.get(listurl % (blogid, currentpage, categoryno))
    s = res.text.replace("\\", "'")
    j = json.loads(s)
    pl = j['postList']
    lognos += list(map(lambda x: x['logNo'], pl))

    currentpage += 1

    if len(pl) < 30:
        break

lognos = list(map(int, lognos[::-1]))
print("Found", len(lognos), "posts.")

def mkdeffiles():
    rmtree("out")
    os.makedirs("out/META-INF")
    os.makedirs("out/OEBPS")
    with open("out/OEBPS/cover.jpg", 'wb') as handler:
        res = rq.get(cover, stream=True)
        handler.write(res.content)

    with open("out/mimetype", 'w') as f:
        f.write("application/epub+zip")

    with open("out/info", 'w') as f:
        f.write("%s %d" % (blogid, categoryno))
        
    with open("out/META-INF/container.xml", 'w') as f:
        f.write(
    """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>""")

    with open("out/OEBPS/cover.xhtml", 'w') as f:
        f.write(
    """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ko">
    <head>
        <title>%s</title>
        <meta charset="UTF-8" />
        <link href="stylesheet.css" type="text/css" rel="stylesheet"/>
        <style type="text/css">
            @page { margin-bottom: 5.000000pt; margin-left: 0; margin-right: 0; margin-top: 5.000000pt; }
        </style>
    </head>

    <body>

        <p class="center">
            <img src="cover.jpg" alt="Cover" class="cover"/>
        </p>

    <p></p>
    </body>
</html>""" % title)

    with open("out/OEBPS/stylesheet.css", 'w') as f:
        f.write(
    """@namespace h "http://www.w3.org/1999/xhtml";
    body {
        margin-bottom: 0;
        margin-left: 5pt;
        margin-right: 5pt;
        margin-top: 0;
        padding-bottom: 0.2em;
        padding-left: 4%;
        padding-right: 4%;
        padding-top: 0.2em;
        page-break-before: always;
        text-align: left;
    }
    h2 {
        display: block;
        width: 100%;
        font-size: 1.6em;
        font-style: normal;
        font-weight: bold;
        line-height: 1.6em;
        margin-bottom: 2.0em;
        margin-left: 0;
        margin-right: 0;
        margin-top: 0;
        padding-bottom: 0;
        padding-left: 0;
        padding-right: 0;
        padding-top: 0;
        page-break-before: always;
        text-align: center;
        text-indent: 0
    }
    p {
        display: block;
        font-size: 0.9em;
        line-height: 1.5em;
        margin-bottom: 0.5em;
        margin-left: 0;
        margin-right: 0;
        margin-top: 0;
        padding-bottom: 0;
        padding-left: 0;
        padding-right: 0;
        padding-top: 0;
        text-align: left;
        text-indent: 0.7em
    }
    .center {
        display: block;
        font-size: 0.9em;
        line-height: 1.5em;
        margin-bottom: 0;
        margin-left: 0;
        margin-right: 0;
        margin-top: 0;
        padding-bottom: 0;
        padding-left: 0;
        padding-right: 0;
        padding-top: 0;
        text-align: center;
        text-indent: 0
        }
    .cover {
        height: auto;
        width: 100%
    }
    .right {
        display: block;
        font-size: 0.9em;
        line-height: 1.5em;
        margin-bottom: 0;
        margin-left: 0;
        margin-right: 0;
        margin-top: 0;
        padding-bottom: 0;
        padding-left: 0;
        padding-right: 0;
        padding-top: 0;
        text-align: right;
        text-indent: 0
        }
    a {
        color: inherit;
        text-decoration: inherit;
        cursor: default
        }
    a[href] {
        color: blue;
        text-decoration: underline;
        cursor: pointer
        }""")

mkdeffiles()

tocncx = open('out/OEBPS/toc.ncx', 'w')
contentopf = open('out/OEBPS/content.opf', 'w')

uid = str(uuid.uuid1())

def wconffilesheader():
    tocncx.write(
"""<?xml version='1.0' encoding='utf-8'?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="ko">
    <head>
        <meta content="%s" name="dtb:uid"/>
        <meta content="2" name="dtb:depth"/>
    </head>
    <docTitle>
        <text>%s</text>
    </docTitle>
    <navMap>
    """ % (uid, title))
    contentopf.write(
"""<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uuid_id">
    <metadata xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:opf="http://www.idpf.org/2007/opf" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:calibre="http://calibre.kovidgoyal.net/2009/metadata" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="uuid_id" opf:scheme="uuid">%s</dc:identifier>
        <dc:title>%s</dc:title>
        <dc:creator>%s</dc:creator>
        <dc:date>2009-04-08</dc:date>
        <dc:language>ko</dc:language>
    </metadata>
    <manifest>
        <item href="cover.jpg" id="cover" media-type="image/jpeg" />
        <item href="cover.xhtml" id="title_1" media-type="application/xhtml+xml" />
"""
    % (uid, title, creator))

wconffilesheader()

for idx, logno in enumerate(lognos, 1):
    # print(logno)
    res = rq.get(baseurl % (blogid, logno))

    # print(res.text)
    a = re.findall(r'<!-- SE.?-TEXT { -->(.+?)<!-- } SE.?-TEXT -->', res.text)
    # print(a)

    b = ''.join(a)

    with open('out/OEBPS/' + str(logno) + '.xhtml', 'w') as f:
        f.write(
"""<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ko">
<head>
	<title>%s</title>
	<meta content="http://www.w3.org/1999/xhtml; charset=utf-8" http-equiv="Content-Type"/>
	<link href="stylesheet.css" type="text/css" rel="stylesheet"/>
	<style type="text/css">
		@page { margin-bottom: 5.000000pt; margin-left: 0; margin-right: 0; margin-top: 5.000000pt; }
	</style>
</head>
<body>""" % title)
        f.write(b.replace("&nbsp;", "").replace("<br>", "<p></p>").replace("<br />", "<p></p>").replace("<br/>", "<p></p>"))
        f.write("</body></html>")
        contentopf.write('        <item href="%d.xhtml" id="%d" media-type="application/xhtml+xml" />\n' % (logno, logno))
        tocncx.write("""
		<navPoint id="%d" playOrder="%d">
			<navLabel>
				<text>%d</text>
			</navLabel>
			<content src="%d.xhtml" />
		</navPoint>
    """ % (logno, idx, logno, logno))

contentopf.write(
    '''         <item href="stylesheet.css" id="css" media-type="text/css" />
        <item href="toc.ncx" id="ncx" media-type="application/x-dtbncx+xml" />'''
    '    </manifest>\n    <spine toc="ncx">\n        <itemref idref="title_1" />\n' 
    + ''.join(map(lambda x: f'        <itemref idref="{x}" />\n', lognos))
    + '    </spine>\n    <guide />\n</package>')

tocncx.write('</navMap>\n</ncx>')

contentopf.close()
tocncx.close()

make_archive(title, "zip", "out", ".")
os.rename("%s.zip" % title, "%s.epub" % title)