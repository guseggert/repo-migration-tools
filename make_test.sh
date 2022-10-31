#!/bin/bash

rm -rf test/
mkdir test
cd test/

mkdir a b
cd a
git init
git commit --allow-empty -m "init"
touch file-a
mkdir dir-a
touch dir-a/a.go
git add file-a dir-a/a.go
git commit -m "add file-a"
git remote add origin .
git reflog --expire=all --expire-unreachable=now --all
git gc --aggressive --prune=now

cd ../b
git init
git commit --allow-empty -m "init"
touch file-b
git add file-b
git commit -m "add file-b"
git remote add origin .
git reflog --expire=all --expire-unreachable=now --all
git gc --aggressive --prune=now
cd ..

