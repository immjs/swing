<p align="center">
  <img width="128" height="128" src="readme/logo.png">
</p>

# Swing

Swing is a modular Desktop Environmnent / Window Manager picker, designed to run on the EPITA PIE.

It allows you to pick between multiple desktop environments upon logging in, and has zero `install.sh` dependencies.

## Setup
Clone this repo into your afs. Then, add this entry into your i3config:
```
exec python 
```
Finally, customize `config.json` to your likings! It will either exist in `~/.config/swing/config.json` or, in the root of this project, at `config.json`

## How it works
Each DE has a list of commands to be run in order to install everything necessary

## Config

### `enabled` (list of strings)
List of enabled DEs. Currently supported:
- `gnome`
- `sway`
- `i3`

Defaults to all of them

### `username` (string)
Username to call you by. Will default to username on computer.

### `close_in` (number)
Delay to wait before closing Swing upon successful launch.

### `autoselect_in` (number)
Delay to wait before automatically selecting a DE for you.

### `prepick` (array of strings)
List of commands to be run before the picker UI is shown.

### `setup` (array of strings)
List of commands to be run before any DE is initialised.

### `additional` (dictionary, values are arrays of strings)
Dictionary, mapping each DE to a list of commands. The commands will be run after the initial setup for this DE has been completed.

### `hide` (list of string)
List of HTML IDs to hide.
