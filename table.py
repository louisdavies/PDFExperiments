import sys
from tabula import convert_into

if len(sys.argv) > 3:
    convert_into(sys.argv[1], sys.argv[2], pages=sys.argv[3],
                    output_format="csv", java_options="-Dfile.encoding=UTF8")
else:
    convert_into(sys.argv[1], sys.argv[2], output_format="csv",
                    java_options="-Dfile.encoding=UTF8")
