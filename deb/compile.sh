#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../vars.sh" "$@"

SRC_DIR="$ROOT_DIR/src"
DEB_DIR="$ROOT_DIR/deb"
RPM_DIR="$ROOT_DIR/rpm"
PKG_DIR="$DEB_DIR/.packaging"
RES_DIR="$DEB_DIR/.result"
BUILDROOT="$DEB_DIR/.artifacts"
DIST_DIR="$BUILDROOT/dist"
DEB_ARCH="$(dpkg --print-architecture 2>/dev/null || echo amd64)"
DEB_ROOT="$BUILDROOT/${NAME}_${COMPILE_VER}-${RELEASE}_${DEB_ARCH}"

echo "==> Building $NAME (Debian/Ubuntu)"
echo "==> Version:    $COMPILE_VER"
echo "==> Release:    $RELEASE"
echo "==> Alias:      $ALIAS"
echo "==> Directory:  $ROOT_DIR"
sleep 1

echo "==> Cleaning old build artifacts"
rm -rf "$BUILDROOT"
rm -rf "$PKG_DIR"
mkdir -p "$BUILDROOT" "$PKG_DIR" "$RES_DIR"

echo "==> Building PyInstaller binaries"
pyinstaller \
  --onefile \
  --distpath "$DIST_DIR" \
  --workpath "$BUILDROOT/service-work" \
  --specpath "$BUILDROOT" \
  --name "${NAME}d" \
  "$SRC_DIR/service.py" & pyinstaller \
  --onefile \
  --distpath "$DIST_DIR" \
  --workpath "$BUILDROOT/cli-work" \
  --specpath "$BUILDROOT" \
  --name "$NAME" \
  "$SRC_DIR/cli.py" & wait

echo "==> Generating shell completion"
ln -sf "$NAME" "$DIST_DIR/$ALIAS"

"$DIST_DIR/$NAME" --print-completion zsh  > "$DIST_DIR/$NAME.zsh"
"$DIST_DIR/$ALIAS" --print-completion zsh > "$DIST_DIR/$ALIAS.zsh"
"$DIST_DIR/$NAME" --print-completion bash > "$DIST_DIR/$NAME.bash"
"$DIST_DIR/$ALIAS" --print-completion bash > "$DIST_DIR/$ALIAS.bash"

rm "$DIST_DIR/$ALIAS"

process_template() {
    sed \
      -e "s/@NAME@/$NAME/g" \
      -e "s/@VERSION@/$COMPILE_VER/g" \
      -e "s/@ALIAS@/$ALIAS/g" \
      -e "s/@RELEASE@/$RELEASE/g" \
      -e "s/@ARCH@/$DEB_ARCH/g" \
      "$1" > "$2"
}

echo "==> Assembling .deb package tree"
mkdir -p "$DEB_ROOT/DEBIAN"
mkdir -p "$DEB_ROOT/usr/libexec/$ALIAS"
mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/usr/lib/systemd/user"
mkdir -p "$DEB_ROOT/usr/lib/udev/rules.d"
mkdir -p "$DEB_ROOT/usr/share/bash-completion/completions"
mkdir -p "$DEB_ROOT/usr/share/zsh/vendor-completions"
mkdir -p "$DEB_ROOT/usr/share/doc/$NAME"

process_template "$DEB_DIR/template.control" "$DEB_ROOT/DEBIAN/control"
process_template "$DEB_DIR/template.postinst" "$DEB_ROOT/DEBIAN/postinst"
process_template "$DEB_DIR/template.postrm" "$DEB_ROOT/DEBIAN/postrm"
chmod 755 "$DEB_ROOT/DEBIAN/postinst" "$DEB_ROOT/DEBIAN/postrm"

install -m 755 "$DIST_DIR/${NAME}d" "$DEB_ROOT/usr/libexec/$ALIAS/${NAME}d"
install -m 755 "$DIST_DIR/$NAME" "$DEB_ROOT/usr/bin/$NAME"
ln -sf "$NAME" "$DEB_ROOT/usr/bin/$ALIAS"

install -m 644 "$DIST_DIR/$NAME.zsh" "$DEB_ROOT/usr/share/zsh/vendor-completions/_$NAME"
install -m 644 "$DIST_DIR/$ALIAS.zsh" "$DEB_ROOT/usr/share/zsh/vendor-completions/_$ALIAS"
install -m 644 "$DIST_DIR/$NAME.bash" "$DEB_ROOT/usr/share/bash-completion/completions/$NAME"
install -m 644 "$DIST_DIR/$ALIAS.bash" "$DEB_ROOT/usr/share/bash-completion/completions/$ALIAS"

process_template "$RPM_DIR/template.service" "$DEB_ROOT/usr/lib/systemd/user/$NAME.service"
cp "$RPM_DIR/llcw.rules" "$DEB_ROOT/usr/lib/udev/rules.d/99-$NAME.rules"

cp "$ROOT_DIR/LICENSE" "$DEB_ROOT/usr/share/doc/$NAME/copyright"
cp "$ROOT_DIR/README.md" "$DEB_ROOT/usr/share/doc/$NAME/README.md"

echo "==> Building .deb"
OS_ID="$(. /etc/os-release && echo "$ID")"
OS_VER="$(. /etc/os-release && echo "$VERSION_ID")"
dpkg-deb --build "$DEB_ROOT" "$RES_DIR/${NAME}-${COMPILE_VER}-${RELEASE}.${OS_ID}${OS_VER}.${DEB_ARCH}.deb"

echo "==> Done!"
