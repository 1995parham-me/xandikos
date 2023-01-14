# Xandikos in Action

## Introduction

[Xandikos](https://github.com/jelmer/xandikos) is a CalDAV/CardDAV server that I use for managing my contacts and calendar events.
This repository contains the required configuration for using it.

## How to?

First you need to have Docker installed and then run Xandikos:

```bash
docker compose up -d

cd user

cd contacts
rm -Rf .git
rm -Rf addressbook
git clone git@github.com/parham-alvani/addressbook

cd calendars
rm -Rf .git
rm -Rf calendar
git clone git@github.com/parham-alvani/calendar
```

Also, you need to add the following information into your contacts/calendar repository:

```
[user]
  name = Parham Alvani
  email = parham.alvani@gmail.com
```

## Repositories

- [addressbook](https://github.com/parham-alvani/addressbook)
- [contacts](https://github.com/parham-alvani/calendar)
