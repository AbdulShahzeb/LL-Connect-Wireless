Name:           @NAME@
Version:        @VERSION@
Release:        1%{?dist}
Summary:        Linux L-Connect Wireless daemon and CLI

License:        MIT
URL:            https://github.com/Yoinky3000/LL-Connect-Wireless
Source0:        %{name}-%{version}.tar.gz

BuildArch:      x86_64

Requires:       libusb1
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

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

# systemd service
install -D -m 644 .packaging/@NAME@.service \
    %{buildroot}/usr/lib/systemd/system/@NAME@.service

# udev rule
install -D -m 644 .packaging/@NAME@.rules \
    %{buildroot}/usr/lib/udev/rules.d/99-@NAME@.rules

%post
%systemd_post @NAME@.service
udevadm control --reload-rules || :
udevadm trigger || :
systemctl enable --now @NAME@.service || :


%preun
%systemd_preun @NAME@.service

%postun
%systemd_postun_with_restart @NAME@.service
udevadm control --reload-rules || :
udevadm trigger || :
systemctl reset-failed @NAME@.service || :
systemctl daemon-reload || :


%files
%license LICENSE
%doc README.md
%dir /usr/libexec/@ALIAS@
/usr/libexec/@ALIAS@/@NAME@d
/usr/bin/@NAME@
/usr/bin/@ALIAS@
/usr/lib/systemd/system/@NAME@.service
/usr/lib/udev/rules.d/99-@NAME@.rules


