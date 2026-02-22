# Maintainer: Yoinky3000
pkgname=@NAME@
pkgver=@VERSION@
pkgrel=@RELEASE@
pkgdesc='Linux L-Connect Wireless daemon and CLI'
arch=('x86_64')
url='https://github.com/Yoinky3000/LL-Connect-Wireless'
license=('MIT')
depends=('libusb' 'systemd' 'bash-completion')
source=("$pkgname-$pkgver.tar.gz")
sha256sums=('SKIP')
install="$pkgname.install"

package() {
    cd "$pkgname-$pkgver"

    # Daemon
    install -Dm755 "dist/${pkgname}d" "$pkgdir/usr/libexec/@ALIAS@/${pkgname}d"

    # CLI + alias
    install -Dm755 "dist/$pkgname" "$pkgdir/usr/bin/$pkgname"
    ln -sf "$pkgname" "$pkgdir/usr/bin/@ALIAS@"

    # Completions
    install -Dm644 "dist/$pkgname.bash" "$pkgdir/usr/share/bash-completion/completions/$pkgname"
    install -Dm644 "dist/@ALIAS@.bash" "$pkgdir/usr/share/bash-completion/completions/@ALIAS@"
    install -Dm644 "dist/$pkgname.zsh" "$pkgdir/usr/share/zsh/site-functions/_$pkgname"
    install -Dm644 "dist/@ALIAS@.zsh" "$pkgdir/usr/share/zsh/site-functions/_@ALIAS@"

    # User-mode systemd service
    install -Dm644 ".packaging/$pkgname.service" "$pkgdir/usr/lib/systemd/user/$pkgname.service"

    # udev rules
    install -Dm644 ".packaging/$pkgname.rules" "$pkgdir/usr/lib/udev/rules.d/99-$pkgname.rules"

    # Docs / license
    install -Dm644 "README.md" "$pkgdir/usr/share/doc/$pkgname/README.md"
    install -Dm644 "LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
