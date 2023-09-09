# NeoTileMap

NeoTileMap is the Blender addon for the Tilemap Builder tool for BallisticNG, adding tilemap based UVing tools into Blender.

## Installing
* Select a release on the right hand side and download it.
* In Blender navigate to `Edit -> Preferences -> Addons`.
* Click `Install` at the top right, select the downloaded ZIP.

Releases are kept up to date if Blender makes breaking changes. If there isn't a release specifically for a newer version of Blender, it's very likely because the addon works in the latest version.

## Developing
NeoTileMap is written in Pycharm Community Edition and contains a build script / run configuration for automatic addon installation, allowing the project to sit separately to a live Blender installation.

### Blender Autocomplete
Download the latest version of [Fake BPY Module](https://github.com/nutti/fake-bpy-module). 

You can use PIP to install this as a package, or download it manually and setup the interpreter paths in Pycharm to include the directory.

### Building
* Run the `build` configuration
* A `build_config.ini` file will be created in the project directory
* Open `build_config.ini` and set `output path` to an absolute path pointing to your Blender's addon folder. If you're using a newer version of Blender, it may be convenient to use script directories.
* Run the `build` configuration again.
* Provided `output path` points to a valid directory that exists, the addons python files will be copied.

### build_config.ini
**`output path`**  : Your Blender addon directory. This is not the path for the addon being copied itself, but the path that all Blender addons are installed into.

**`name`**         : The name of the addon. This is used for the sub-directory name when copying files.

**`archive`**      : Whether to write a ZIP file for addon distribution. This can be provided for people to use the `install` button in Blender's addon manager.
