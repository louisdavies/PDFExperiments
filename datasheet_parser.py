import sys
import os
import pdfminer
import csv
import subprocess
import io
import re
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import HTMLConverter,TextConverter,XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from PyPDF2 import PdfFileWriter, PdfFileReader
from tabula import convert_into

MU_CHAR = 'u'

GLOBAL_SEARCHES = {'Milliamps':r'(\d*[\.]*\d+)\s*m\s*A',
                    'Microamps':r'(\d*[\.]*\d+)\s*[{}\?]\s*A'.format(MU_CHAR),
                    'Microamps2':r'((?:\d*[\.]*\d+\s*)+)[{}\?]\s*A'.format(MU_CHAR),
                    
                    'Frequency':r'(\d*[\.]*\d+).*Hz'}



class Datasheet():
    def __init__(self, folder, filename, already_split=False, **kwargs):
        self.folder = folder
        self.filename = filename
        self.results = {x : [] for x in GLOBAL_SEARCHES}
        self.split = already_split
        self.subfolder = "temp"
        self.numPages = 34
        if 'searches' in kwargs:
            # self.split_pdf()
            self.perform_searches(kwargs['searches'])
        elif 'split_pdf' in kwargs:
            self.split_pdf()

    def path(self):
        return '/'.join([self.folder, self.filename])
    
    def raw_filename(self):
        return self.filename.split('.')[0]

    def split_pdf(self, subfolder="temp"):
        self.subfolder = subfolder
        try:
            os.mkdir('/'.join([self.folder, self.subfolder]))
        except OSError:
            pass
        except Exception as e:
            print(e)

        print("Splitting {}".format(self.filename))
        with open(self.path()(), "rb") as f:
            inputpdf = PdfFileReader(f)
            self.numPages = inputpdf.numPages
            for i in range(self.numPages):
                output = PdfFileWriter()
                output.addPage(inputpdf.getPage(i))
                doc_name = "{}-page{}.pdf".format(self.raw_filename(), i+1)
                out_path = '/'.join([self.folder, self.subfolder, doc_name])
                with open(out_path, "wb") as outputStream:
                    output.write(outputStream)
                sys.stdout.write('.')
                sys.stdout.flush()
            print()
        self.split = True

    def perform_searches(self, searches=None):
        if searches:
            self.searches = searches
        if not self.split:
            self.split_pdf()
        self.try_search(self.searches)
        
    def try_search(self, searches):
        tempdir = '/'.join([self.folder, self.subfolder])
        for page in range(self.numPages):
        # for filename in os.listdir(tempdir):
            try:
                # print(filename)
                self.find_in_page(page+1, searches)
            except pdfminer.pdfparser.PDFSyntaxError as e:
                print(e)
            except pdfminer.pdfdocument.PDFTextExtractionNotAllowed as e:
                print(e)
            except pdfminer.psparser.PSEOF as e:
                print(e)
            # except Exception as ex:
            #     template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            #     message = template.format(type(ex).__name__, ex.args)
            #     print(message)
             # print(os.path.join(directory, filename))
        return

    def process_results(self, match, page, search):
        # values = match.group(1)
        # for value in re.finditer(r'(\d*[\.]*\d+)', values):
        result = Result(match, page, search)
        print(result)
        self.results[search].append(result)
        # return

    def find_in_page(self, page, searches=None):
        progress = 'Processing page {} / {}'.format(page, self.numPages)
        print(progress)

        raw_text_output = self.text_from_pdf_general(self.path(), page=page-1)
        raw_name = "{}-page-{}".format(self.raw_filename(), page)
        table_format_output = self.text_from_pdf_tables(self.path(),
                                                        str(page),
                                                        "{}.csv".format(raw_name))

        table_format_output = ''
        output = '\n'.join([raw_text_output, table_format_output])
        # print(output)

        for search in searches:
            for line in output.split("\n"):
                if line == '': continue
                if len(line) < 5: continue
                regex_search = GLOBAL_SEARCHES[search]
                match = re.search(regex_search, line)
                # print(line)
                if match:
                    self.process_results(match, page, search)

    def list_results(self):
        results = []
        for search in self.searches:
            for match in self.results[search]:
                results.append(match)
        if results == []:
            return False
        return results

    def text_from_pdf_tables(self, filename, page="all", csv_name="temp.csv"):
        try:
            out = subprocess.check_output(["python", "table.py", filename, csv_name, page],
                                            stderr=subprocess.DEVNULL)
                                            # timeout=10)
        except:
            print('text_from_pdf_tables FAILED')
            pass
            # assert False, "Table error"
        text = '\n'.join(load_csv(csv_name))
        return text

    def text_from_pdf_general(self, filename, page="0"):
        try:
            out = subprocess.check_output(["python", "text.py", filename, str(page)],
                                            stderr=subprocess.DEVNULL, timeout=5)
            return out.decode(errors="ignore")
        except:
            pass
        return 'text_from_pdf_general FAILED'


class Result():
    def __init__(self, match, line, search):
        self.match = match
        self.line = line
        self.search = search
        # self.file = file

    def __repr__(self):
        properties = ["Search term: '{}'".format(self.search),
                        "value: '{}'".format(self.match.group(0)),
                        "page: {}".format(self.line)]
        return ', '.join(properties)


def get_text(filename, pages=None):
    text = convert_pdf_to_txt(filename, pages)
    output = ''
    with open('output.txt', "w") as f:
        for line in text:
            try:
                if line == '\u03bc':
                    output += MU_CHAR
                elif line == 'µ':
                    output += MU_CHAR
                else:
                    f.write(line)
                    output += line
            except:
                pass
    return output


def load_csv(filename):
    result = []
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            result.append(' '.join(row))
            #print(result[-1])
    return result

def convert_pdf_to_txt(path_to_file, pages=None):
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path_to_file, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    if pages:
        # pagenos=set(pages)
        pagenos=set()
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
    print(text)
    # return text



# print('0.54 μA')
# print("µ")
def clean_up():
    folder = "temp_pdf"
    for filename in os.listdir(folder):
        path = '/'.join([folder, filename])
        if re.search(r"-page\d+\.pdf", filename):
            os.remove(path)
    

def main(split=True):
    searches = ['Milliamps',
                'Microamps',
                'Frequency']
    # searches = ['Microamps']
    folder = "temp_pdf"
    sheets = []

    result_folder = "hits"

    for filename in os.listdir(folder):
        if filename.endswith('.pdf'):
            # try:
            sheets.append(Datasheet(folder, filename, already_split=True, searches=searches))
            if sheets[-1].list_results():
                print(sheets[-1].list_results())
                try:
                    os.rename('/'.join([folder, filename]),
                        '/'.join([folder, result_folder, filename]))
                except:
                    print("Couldn't move {}. But searching done.".format(filename))
            # except Exception as e:
            #     print(e)


if __name__ == "__main__":

    main(split=False)
    # clean_up()
