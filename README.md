# Knot's Stages and Mods

***Note**: Please see "Postmortem" for history and notes.*

This repository contains the assets, build scripts and packages for **Knot's Stages and Mods**, also known as **Knot's Update**.

It is not maintained anymore, but I guess it could be fun to look thorugh for some "internet people," especially because it was the slighest bit popular for no good reason (I would have rather it not been, though).

## Pre-Build

You will need a Knot's Stages and Mods APK that already has all the files, since not all of them are in this repo.

You can find one here: [Google Drive Link to KSAM 1.4.4 APK](https://drive.google.com/file/d/1VcTbgK23PQhlBZTMdKEOGbn5Y78fKwON/view).

**Note**: That verison also contains some changes I had made when playing with a new mesh baker that never got finsihed. I don't keep old verisons of mods, so I can't provide a "clean" version of KSAM.

## Building

To start building, open an exsisting build of KSAM in [APK Editor Studio](https://qwertycube.com/apk-editor-studio/). Open the contents and copy the path to where the temp files are. After this, run:

```sh
$ python3 ./build.py $APKROOT
```

Where `$APKROOT` is where the path to the files are. This will copy over the files.

Now, save the APK that you opened. The resulting APK should match what a normal KSAM would be.

### Note About Using APKTool

It is possible to use any tool, like `apktool`, and just provide the path to the root of the APK to the build script. The build script just does a dumb file copy to overlay the files onto the new APK.

## Postmortem

### Summary Portion

Ultimately, this whole repository (and the early Smash Hit modding community in general) is quite symbolic for me. This is the first time I ever sat down and did something to at least half completeion, and it was my first "real project." This project forced me to learn a bit of OpenGL and understand a bit of how graphics work (to which I am still learning the basics of today). It helped me get a vaugely better grasp on how images are stored, even if I was shown [how it's actually done](https://github.com/SamusAranX/mtxconv#general-format-information) a bit more recently. And I think more importantly, it was my first project that I actually showed other people.

Ignoring all of the positives, I will admit that every part of this project - from the stages to the actual tools I wrote - are pretty bad and really, really only "get the job done" rather than "get the job done *well*." I still suffer from not putting enough effort into my implementations of concepts (I have always been one more for the idea of something rather than it's implementation), though I am trying to work on that, slowly. 

Unforulately, this project shows my "idea over implementation" mindset as raw as it could possibily get. The stages look pretty barebones, even after I tried to add some columns and decor to them to make them look good. The build system is fairly barebones and garbage. Blender Tools were never that good and missed supporting a lot of features while breaking anytime there was a major update. (When I opened blender in a console I think I must have got 30 deprecation warnings or so while the tool was enabled...) MTXBake was maybe okay-ish in concept (as I remember it) but as stated earlier my understanding of how MTX images were stored was not good at all so there were many errors when displaying images on some devices.

I hope you can understand that this repo has more value to me (and maybe by a longshot others) than what it appears to have on the surface; that's mainly becuase of the meaning that surrounds it and not what the end product is. Maybe you can make something useful out of it or continue the mod in some form - I would be happy to see the result.

### The Notes

  * Often times I would commit test versions, or commited changes that I knew weren't going to make it in, without using branches or anything like that.
  * The build system uses a very basic "packages" system, where there is a `package.json` file in each folder. This was going to be used to provide info about the build as well as provide adding and removing mods on the fly.
  * The `unused` folder contains the segment that was used on the initial test of Blender Tools.
  * The `util` folder has some of the old utilites that the build system might have made use of, as well as an extra two versions of Blender Tools that were customised for use with KSAM. The one called `blender_tools.py` was the frist version with lighting support that also allowed using "legacy lighting" (e.g. none).
  * The `main` folder also has some intresting things, mainly any files that needed to be overridden went here. It contains the menu images as well as the customised shaders that the mod uses.
  * The folder named `rgn` contains the random room generator, which it seems I made slight updates to at some time. This is the folder to look in if you are instrested in that. At some point, I was planning to make the generator more of a framework that would be easy to add custom obstacles to and otherwise make a better endless mode in other mods, but this never really happened.
  * While the `start` folder contains the purple river segments, the `work` folder contains segments that would have been used for the original start. It was named `work4` sometimes since it was meant to be a continuation of the numbering of work folders found in the beta builds of the game.
  * There are the original source files for all of the logos in `textures/menu`.
