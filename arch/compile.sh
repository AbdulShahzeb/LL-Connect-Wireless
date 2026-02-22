#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../vars.sh" "$@"

SRC_DIR="$ROOT_DIR/src"
ARCH_DIR="$ROOT_DIR/arch"
RPM_DIR="$ROOT_DIR/rpm"
PKG_DIR="$ARCH_DIR/.packaging"
RES_DIR="$ARCH_DIR/.result"
BUILDROOT="$ARCH_DIR/.artifacts"
DIST_DIR="$BUILDROOT/dist"
MAKEPKG_DIR="$BUILDROOT/makepkg"

# Arch pkgver cannot contain tilde.
ARCH_PKGVER="${COMPILE_VER//\~/}"

echo "==> Building $NAME (Arch Linux)"
echo "==> Version:    $ARCH_PKGVER"
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
      -e "s/@VERSION@/$ARCH_PKGVER/g" \
      -e "s/@ALIAS@/$ALIAS/g" \
      -e "s/@RELEASE@/$RELEASE/g" \
      "$1" > "$2"
}

echo "==> Preparing Arch package source tree"
process_template "$RPM_DIR/template.service" "$PKG_DIR/$NAME.service"
cp "$RPM_DIR/llcw.rules" "$PKG_DIR/$NAME.rules"
process_template "$ARCH_DIR/template.PKGBUILD" "$PKG_DIR/PKGBUILD"
process_template "$ARCH_DIR/template.install" "$PKG_DIR/$NAME.install"

SRCROOT="$BUILDROOT/$NAME-$ARCH_PKGVER"
mkdir -p "$SRCROOT"
cp -a "$DIST_DIR" "$SRCROOT/"
cp -a "$PKG_DIR" "$SRCROOT/.packaging"
cp "$ROOT_DIR/README.md" "$SRCROOT/"
cp "$ROOT_DIR/LICENSE" "$SRCROOT/"

tar czf "$PKG_DIR/$NAME-$ARCH_PKGVER.tar.gz" -C "$BUILDROOT" "$NAME-$ARCH_PKGVER"

echo "==> Building Arch package"
mkdir -p "$MAKEPKG_DIR"
cp "$PKG_DIR/PKGBUILD" "$MAKEPKG_DIR/"
cp "$PKG_DIR/$NAME.install" "$MAKEPKG_DIR/"
cp "$PKG_DIR/$NAME-$ARCH_PKGVER.tar.gz" "$MAKEPKG_DIR/"

cd "$MAKEPKG_DIR"
if [ "$EUID" -eq 0 ]; then
    useradd -m builduser 2>/dev/null || true
    chown -R builduser: "$MAKEPKG_DIR"
    su builduser -c "cd '$MAKEPKG_DIR' && makepkg -f --nodeps"
else
    makepkg -f --nodeps
fi

find "$MAKEPKG_DIR" -name "*.pkg.tar.zst" -exec cp {} "$RES_DIR/" \;

echo "==> Done!"
