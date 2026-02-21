Name:           @NAME@
Version:        @VERSION@
Release:        @RELEASE@%{?dist}
Summary:        Linux L-Connect Wireless daemon and CLI

License:        MIT
URL:            https://github.com/Yoinky3000/LL-Connect-Wireless
Source0:        %{name}-%{version}.tar.gz

BuildArch:      x86_64

Requires:       libusb1
Requires:       bash-completion
%{?systemd_requires}

%global debug_package %{nil}

%description
User-space daemon and CLI for controlling Lian Li Wireless fans on Linux.

%prep
%setup -q

%build
# binaries already built by PyInstaller

%install
rm -rf %{buildroot}

# Daemon
install -D -m 755 dist/@NAME@d \
    %{buildroot}/usr/libexec/@ALIAS@/@NAME@d

# CLI
install -D -m 755 dist/@NAME@ \
    %{buildroot}/usr/bin/@NAME@
ln -sf @NAME@ %{buildroot}/usr/bin/@ALIAS@

# create auto completion
install -Dm644 dist/@NAME@.zsh %{buildroot}/usr/share/zsh/site-functions/_@NAME@
install -Dm644 dist/@ALIAS@.zsh %{buildroot}/usr/share/zsh/site-functions/_@ALIAS@

install -Dm644 dist/@NAME@.bash %{buildroot}/usr/share/bash-completion/completions/@NAME@
install -Dm644 dist/@ALIAS@.bash %{buildroot}/usr/share/bash-completion/completions/@ALIAS@

# systemd service
install -D -m 644 .packaging/@NAME@.service \
    %{buildroot}/usr/lib/systemd/user/@NAME@.service

# udev rule
install -D -m 644 .packaging/@NAME@.rules \
    %{buildroot}/usr/lib/udev/rules.d/99-@NAME@.rules

%post
udevadm control --reload-rules || :
udevadm trigger || :


%postun
udevadm control --reload-rules || :
udevadm trigger || :


%files
%license LICENSE
%doc README.md
%dir /usr/libexec/@ALIAS@
/usr/libexec/@ALIAS@/@NAME@d
/usr/bin/@NAME@
/usr/bin/@ALIAS@
/usr/share/zsh/site-functions/_@NAME@
/usr/share/zsh/site-functions/_@ALIAS@
/usr/share/bash-completion/completions/@NAME@
/usr/share/bash-completion/completions/@ALIAS@
/usr/lib/systemd/user/@NAME@.service
/usr/lib/udev/rules.d/99-@NAME@.rules


