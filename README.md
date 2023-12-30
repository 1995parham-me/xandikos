<h1 align="center"> Xandikos in Action </h1>
<h6 align="center"> Calendar and Contacts in Git without any 3rd-party services </h6>

## Introduction

[Xandikos](https://github.com/jelmer/xandikos) is a CalDAV/CardDAV server that I use for managing my contacts and calendar events.
This repository contains the required configuration for using it.

## How to?

First you need to have Docker installed and then run Xandikos with the provided `docker-compsoe`:

```bash
docker compose up -d
```

After that it automatically creates required file structure, and you need to replace its bare
repositories with your actual repositories:

```bash
cd user

cd contacts
rm -Rf .git
rm -Rf addressbook
git clone git@github.com:parham-alvani/addressbook

cd ..

cd calendars
rm -Rf .git
rm -Rf calendar
git clone git@github.com:parham-alvani/calendar
```

Also, you need to add the following information into your contacts/calendar git repository:

```ini
[user]
  name = Parham Alvani
  email = parham.alvani@gmail.com
```

Xandikos automatically creates commits and with this information you will have commits with your name and email address
that can be pushed on GitHub without any issues.

## Using it with [`khal`](https://github.com/pimutils/khal) and [`khard`](https://github.com/lucc/khard)

For putting `khal` and `khard` into work when they configured to use another address as their repositories,
you can use the following symbolic links:

```bash
cd /home/parham/Documents/Git/parham/parham-alvani

ln -s ~/Downloads/xandikos/user/contacts/addressbook addressbook
ln -s ~/Downloads/xandikos/user/calendars/calendar calendar
```

## Repositories

- [addressbook](https://github.com/parham-alvani/addressbook)
- [contacts](https://github.com/parham-alvani/calendar)
