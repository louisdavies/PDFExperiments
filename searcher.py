
import requests 
from googlesearch import search
import ssl
import pdf2txt

# to search 
query = "low power hall sensor datasheet"

folder = "temp_pdf"
number = 100

file_list = []
def main():
    for j in search(query, tld="co.in", stop=number, pause=1): 
        #print(j)
        if j[-4:] == ".pdf":
            print(j)
            filename = j.split('/')[-1]
            path = '/'.join([folder, filename])
            file_list.append(path)
            try:
                r = requests.get(j, stream = True)
                with open(path, 'wb') as pdf:
                    n = 0
                    for chunk in r.iter_content(chunk_size=4*1024): 
                        # writing one chunk at a time to pdf file 
                        if chunk: 
                            pdf.write(chunk)
                            # print(n)
                            n += 1
            except ssl.CertificateError as e:
                print(e)
            except requests.exceptions.SSLError as e:
                print(e)
                # rllib3.exceptions.MaxRetryError

print(type(float("1.0")))