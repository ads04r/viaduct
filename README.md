# Viaduct

A bridge across [Arches](https://github.com/archesproject/arches)

## Purpose

[Our group](https://github.com/achp-project) is involved in the
maintenance of several independent self-hosted instances of the
[Arches](https://github.com/archesproject/arches) Cultural Heritage
platform. The data contained within these instances all comply to
project-specific vocabularies, making the creation of a single
Arches instance for all the data a hard problem. Viaduct seeks to
bypass the problem altogether by acting as a standalone portal for
multiple Arches instances, allowing a user to perform one search
on several instances at once, and return a unified results page.

## Demo

Currently you can see the software in action at https://viaduct.drashsmith.com/

## Installation

To install your own instance, first clone the repository

```bash
git clone https://github.com/marea-project/viaduct.git
cd viaduct
```

Create a virtual environment and install the dependencies using pip

```bash
mkdir .venv
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create a local settings file at `viaduct/settings_local.py`. You
can use the `settings_local.py.sample` within the repository as
a template.

Set up the database by running the migrations

```bash
python manage.py migrate
```

Create an admin user...

```bash
python manage.py createsuperuser
```

Finally, run the development server.

```bash
python manage.py runserver 0:8000
```

## Adding data sources

Next you need to add one or more Arches instances to search. To do this, access
the API in a web browser by going to `http://localhost:8000/api`. Log in
using the link at the top, then go to `http://localhost:8000/api/instances/`.
From here you can use the Django REST Framework default UI to add Arches instances.

### Populating vocabularies

Once you've added some instances, you can import a copy of their vocabularies into
Viaduct. To do this, from the command line, type...

```bash
python manage.py import_vocabularies
```

You should now see the concepts that your imported instances understand from the
Viaduct API.

