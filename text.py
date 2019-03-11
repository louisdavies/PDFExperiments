import io
import sys
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import HTMLConverter,TextConverter,XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
# import pdfminer


def convert_pdf_to_txt(path_to_file, pages=None):
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-16'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path_to_file, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    if pages:
        pagenos=set(pages)
    else:
        pagenos=set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages,
                                    password=password, caching=caching,
                                    check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text

if __name__ == "__main__":
    # text = convert_pdf_to_txt(sys.argv[1])
    text = convert_pdf_to_txt(sys.argv[1], pages=[int(sys.argv[2])])
    output = ''
    with open('output.txt', "w") as f:
        for line in text:
            try:
                if line == '\u03bc':
                    output += MU_CHAR
                elif line == 'µ':
                    output += MU_CHAR
                else:
                    # f.write(line)
                    output += line
            except:
                pass
    print(output)