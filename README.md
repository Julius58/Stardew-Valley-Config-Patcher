# Config Patcher for Stardew Valley

## Overview

The **Config Patcher for Stardew Valley** is a command-line tool designed to manage configuration patches for Stardew Valley mods. This script allows you to either create a new patch file or apply existing patches to a specified configuration mod. It supports generating a new patch from provided configuration files and existing patches, helping you efficiently manage and apply mod configurations for your Stardew Valley game.

## Features

- **Create a New Patch**: Generate a new patch file from provided config files and existing patches.
- **Apply Existing Patches**: Apply all provided patches to the specified config mod or create a new one if it doesn't exist.

## Installation

Ensure you have Python 3.12 or later installed on your system (*Only tested with Python 3.12*). Follow these steps to set up the Config Patcher:

1. Clone or download the repository and navigate to the directory where the script is located:

   ```bash
   git clone https://github.com/Julius58/Stardew-Valley-Config-Patcher
   cd Stardew-Valley-Config-Patcher
   ```

2. Install dependencies using the provided `install.bat` batch script.


3. Install **Config Patches.zip** using Vortex:

   - Ensure the Mod Type is set to `sdvrootfolder`.
   - Deploy the mod to your Stardew Valley installation.

## Usage

To use the Config Patcher, run the batch file `run.bat` with the desired arguments. Below are the available command-line options:

### Arguments

- `--create`

  - **Type**: `flag` (boolean)
  - **Default**: `False`
  - **Description**: Changes the mode to create a new patch file from all provided config files and existing patches. If this flag is set, the script will generate a new patch file rather than applying existing patches.
- `--close`

  - **Type**: `flag` (boolean)
  - **Default**: `False`
  - **Description**: Closes the script immediately after completion without waiting for user input.

### Examples

#### Create a New Patch

To create a new patch file, use the `--create` flag. This will generate a patch file based on the provided configuration files and existing patches.

```bash
python config_patcher.py --create
```

#### Apply Existing Patches

To apply existing patches, run the script without any arguments. The script will apply all provided patches to the specified config mod or create a new one if it doesn't exist.

```bash
python config_patcher.py
```

## Contributing

Feel free to open issues or submit pull requests if you have improvements or bug fixes. Contributions are welcome!

## License

This project is licensed under the CC0. See the [LICENSE](LICENSE) file for details.
