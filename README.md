<h1 align="center"> Xandikos in Action </h1>
<h6 align="center"> Calendar and Contacts in Git without any 3rd-party services </h6>

<p align="center">
    <img src=".github/logo.png" alt="logo" height="200px" />
</p>

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

rm -rf addressbook
rm -rf calendar

ln -s ~/Downloads/xandikos/user/contacts/addressbook addressbook
ln -s ~/Downloads/xandikos/user/calendars/calendar calendar
```

## Regenerate TLS Certificates

macOS required TLS for its CardDav account, so we need to support HTTPS over Xandikos.
The main step here is to generate the certificate using the following command:

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes -subj "/C=IR/ST=Tehran/L=Tehran/O=1995parham-me/OU=davx/CN=davx.infra.1995parham.me"
```

[Reference](https://stackoverflow.com/questions/10175812/how-to-generate-a-self-signed-ssl-certificate-using-openssl)

## Repositories

- [addressbook](https://github.com/parham-alvani/addressbook)
- [contacts](https://github.com/parham-alvani/calendar)
