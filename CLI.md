# CLI Documentation

## `ll-connect-wireless`

```bash
usage: gen_cli_doc.py [-h] [--print-completion {bash,zsh,tcsh}]
                      {help,info,update,status,enable,disable,start,stop,restart,monitor,uninstall,settings} ...

LL-Connect-Wireless (LLCW) CLI (Version: 0.0.0)

positional arguments:
  {help,info,update,status,enable,disable,start,stop,restart,monitor,uninstall,settings}
                        Available commands
    help                same as -h/--help
    info                show app version info and changelog of llcw
    update              check and update llcw to latest version
    status              show systemd service status
    enable              enable llcw service and start it
    disable             disable llcw service
    start               start the llcw service
    stop                stop the llcw service
    restart             restart the llcw service
    monitor             show live fan monitor (Default to it if no command is provided)
    uninstall           stop, disable and remove llcw
    settings            Manage settings

options:
  -h, --help            show this help message and exit
  --print-completion {bash,zsh,tcsh}
                        print shell completion script

'llcw' is also an alias command to 'll-connect-wireless'. You can also use 'll-connect-
wireless' without arguments to see live monitor.
```

## `ll-connect-wireless settings`

```bash
usage: gen_cli_doc.py settings [-h] {set-mode,reset,linear} ...

positional arguments:
  {set-mode,reset,linear}
    set-mode            set control mode
    reset               reset the settings
    linear              Linear mode settings

options:
  -h, --help            show this help message and exit
```

## `ll-connect-wireless settings linear`

```bash
usage: gen_cli_doc.py settings linear [-h] {reset,set-curve} ...

positional arguments:
  {reset,set-curve}
    reset            reset linear curve
    set-curve        set linear curve

options:
  -h, --help         show this help message and exit
```
