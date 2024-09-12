# ESNcards generator

This tools serves help for ESN sections to mass produce ESNcards, it gets input data from `.csv` file downloaded from Application Google Form, downloads uploaded photos of applications, and generates `.pdf` as print resources. 

## How to produce cards
### Installation
Install all requirements into your python3 environment -- all listed in `requirements.txt`.

```bash
apt install python3 python3-venv pyton3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Download data from gForm
Download form responses in .csv format, expected headers:

* `Timestamp`in ISO format
* `Email`
* `Name and Surname  (e.g. Walter White)`
* `Country (e.g. Mexico)`
* `Date of Birth (e.g. 07/09/98)`
* `Upload a passport-sized photo of yourself (2.7x3.7 cm)` as google drive link

> **_NOTE:_** The script expects data in certain columns. See `config.py` if you edit
the Application form and data are in different columns. This usually happens with each new board. :)

> **_NOTE:_** Remove any lines from the .csv file that are note the names - eg. empty rows
and the column names (Name, Email, ...)


### Download photos

File `client_secret.json` (placed in project root) is needed to access Google Drive, you can get one from
[Google APIs](https://console.developers.google.com/apis/credentials), especially
OAuth 2.0
Client IDs (with all Google Drive perms) for your own project.
This only needs to be done once in the beginning.

Then run the following command:

```
python3 download_images.py <downloaded_form_file>.csv
```

In case of unknown format, photo is stored in project root. Before next steps, it's needed to reformat the file and move into `pictures` directory under the same name.

### Generating ESNcard print files

So the typical usage would be:

To render just labels to print them on transparent foil, output is `output-text.pdf`:
```
./generate.py --mode text
```

To render just photos to print, output is `output-photo.pdf`:
```
./generate.py --mode photo
```

In photo mode, the script sometimes detects multiple faces. U need to looks in folder `decisions/`
to see which of the detections is an actual face. Then in the command line write the number of
the detection.

## Authors
* IT department of ESN VUT Brno:
* [Jozef Zuzelka](https://github.com/jzlka)
* [Joe Kolář](https://github.com/thejoeejoee)
* [Roman Krček](https://github.com/erman-dev)

## Sample outputs

### Output of photos, printed on white paper/photopaper
![photo-1](https://user-images.githubusercontent.com/6154740/153076979-541d7e68-5330-43c3-9e46-b239153d04d4.png)
### Output of labels, printed on transparent foil
![text-1](https://user-images.githubusercontent.com/6154740/153076981-f09c691d-9944-4cb4-8804-a5072b7aff59.png)
