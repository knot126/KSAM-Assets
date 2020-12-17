# Knot's Stages and Mods

This repository contains the assets, build scripts and packages for Knot's Stages and Mods.

## Building

To start building, open an exsisting build of KSAM in APK Editor Studio. Open the contents and copy the path to where the temp files are. After this, run:

```sh
$ python3 ./build.py $APKROOT
```

Where `$APKROOT` is where the path to the files are. This will copy over the files.

## Why you need an existing APK

Not all of the files are actually included in this repositiory for space-saving reason (and it technically wouldn't be legal to do that, either). Here is a short list of missing files that should be added later:

* The launcher icon
* Modified main menu lua files
* Generator room
* `game.xml`

## Notes and To-Do

* The build system is quite messy, mainly because it doesn't take advantage of packages enough.
* The jungle stage needs to be split into its own package.
* The "unused" directory contains files I don't want in my documents folder anymore.
