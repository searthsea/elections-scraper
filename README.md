# Description
This is a simple tool for scraping Czech parliamentary election results (specifically 2017 elections). The script outputs a .csv file with the elections results.

## Requirements
You will need to install bs4 and requests modules to run the script. See version details in the requirements.txt file.

## Running the scraper
Run the script in the terminal using the main.py file with 2 positional arguments, like so:
``` cmd
python main.py <election-district-url> <export-filename.csv>
```
**Important:** The scraper works only with URL arguments, that are listed in rightmost column [here](https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ).  

### Export data struture
The output .csv file contains the election results of all political parties in each municipality within the selected district (=okres).
Each row represents election results in one municipality.
From column 6 to the right, you'll find number of valid votes for each party with candidates in the municipality.
Text labels in html tree are originally in Czech; the export columns labels are in English. Data are structured as follows:

csv | html
---|-----------
id | číslo obce
municipality | název obce
registred | voliči v seznamu
envelopes | vydané obálky
valid | platné hlasy
name of the political party | počet platných hlasů pro jednotlivé strany

## Example usage

The election results in the Blansko disctrict - positional args:
1. arg (url): ```"https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6201"```
2. arg (filename): ```results-blansko.csv```

Run script in the terminal:
```python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6201" results-blansko.csv```

Script is running:
``` 
Scraping municipal data...
OK
Export successfully completed: results-blansko.csv
Execution time: 18.713 sec
```

Results preview:

```
id,municipality,registred,envelopes,valid,(...political party names...)
581291,Adamov,3668,2157,2138,208,3,5,222,0,76,241,37,18,28,1,7,208,5,63,565,5,14,117,2,10,3,6,278,15,1
581313,Bedřichov,205,155,153,16,0,2,10,0,3,4,0,3,8,0,0,13,0,6,51,0,1,17,0,0,1,0,18,0,0
...
```

