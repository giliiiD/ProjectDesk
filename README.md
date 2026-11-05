# ProjectDesk

Windows application for project based work: every project has todos, notes and links, with formatted text, images and attachments. Entries, groups and whole projects can be shared with colleagues as `.pdesk` files.

![ProjectDesk](docs/screenshot.png)

## Installation

Download `ProjectDesk_Setup.exe` from the latest release and run it. No administrator rights are needed. An existing ToDo installation is updated, the data is kept.

## User Manual

See [ProjectDesk User Manual](docs/ProjectDesk_User_Manual.pdf).

## Build

Releases are built on GitHub: the workflow Release builds the installer on Windows and publishes it with the user manual, see [DEVELOPMENT.md](DEVELOPMENT.md).

For a local build: Python 3 and Inno Setup are required. Run `build.bat`, the installer is created at `installer\ProjectDesk_Setup.exe`.

## Development

[DEVELOPMENT.md](DEVELOPMENT.md) is the project documentation: purpose, architecture, data format, design rules, testing, release steps and version history. To extend ProjectDesk in a new chat or as a new developer, start with its section "Quick Start for a New Chat" and provide `DEVELOPMENT.md` together with `project_desk.py`.

---

Version 2.1.0  
Daniel Gilinberg
