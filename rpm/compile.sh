#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT_DIR/../vars.sh" "$@"

SRC_DIR="$ROOT_DIR/src"
RPM_DIR="$ROOT_DIR/rpm"
PKG_DIR="$RPM_DIR/.packaging"
RES_DIR="$RPM_DIR/.result"
BUILDROOT="$RPM_DIR/.artifacts"
DIST_DIR="$BUILDROOT/dist"

echo "==> Building $NAME"
echo "==> Version:    $COMPILE_VER"
echo "==> Release:    $RELEASE"
echo "==> Alias:      $ALIAS"
echo "==> Directory:  $ROOT_DIR"
sleep 1

echo "==> Cleaning old build artifacts"
rm -rf "$BUILDROOT"
rm -rf "$PKG_DIR"
mkdir "$PKG_DIR"
mkdir -p "$RES_DIR"
rm -rf ~/rpmbuild/RPMS/*

echo "==> Building PyInstaller binaries"

pyinstaller \
  --onefile \
  --clean \
  --distpath "$DIST_DIR" \
  --workpath "$BUILDROOT/pyinstaller-work" \
  --specpath "$BUILDROOT" \
  --name "${NAME}d" \
  "$SRC_DIR/service.py"

pyinstaller \
  --onefile \
  --clean \
  --distpath "$DIST_DIR" \
  --workpath "$BUILDROOT/pyinstaller-work" \
  --specpath "$BUILDROOT" \
  --name $NAME \
  "$SRC_DIR/cli.py"

echo "==> Generating Auto Complete"

ln -sf "$NAME" "$DIST_DIR/$ALIAS"

# Zsh
"$DIST_DIR/$NAME" --print-completion zsh  > "$DIST_DIR/$NAME.zsh"
"$DIST_DIR/$ALIAS" --print-completion zsh > "$DIST_DIR/$ALIAS.zsh"

# Bash
"$DIST_DIR/$NAME" --print-completion bash > "$DIST_DIR/$NAME.bash"
"$DIST_DIR/$ALIAS" --print-completion bash > "$DIST_DIR/$ALIAS.bash"

rm "$DIST_DIR/$ALIAS"

echo "==> Preparing RPM source tree"

sed \
  -e "s/@NAME@/$NAME/g" \
  -e "s/@VERSION@/$COMPILE_VER/g" \
  -e "s/@ALIAS@/$ALIAS/g" \
  -e "s/@RELEASE@/$RELEASE/g" \
  $RPM_DIR/template.service \
  > $PKG_DIR/$NAME.service
sed \
  -e "s/@NAME@/$NAME/g" \
  -e "s/@VERSION@/$COMPILE_VER/g" \
  -e "s/@ALIAS@/$ALIAS/g" \
  -e "s/@RELEASE@/$RELEASE/g" \
  $RPM_DIR/template.spec \
  > $PKG_DIR/$NAME.spec
cp $RPM_DIR/llcw.rules $PKG_DIR/$NAME.rules

SRCROOT="$BUILDROOT/$NAME-$COMPILE_VER"
mkdir -p "$SRCROOT"

cp -a "$DIST_DIR" "$SRCROOT/"
cp -a "$PKG_DIR" "$SRCROOT/"
cp $ROOT_DIR/README.md "$SRCROOT/"
cp $ROOT_DIR/LICENSE "$SRCROOT/"

echo "==> Generating Tar"

tar czf "$PKG_DIR/$NAME-$COMPILE_VER.tar.gz" -C "$BUILDROOT" "$NAME-$COMPILE_VER"

echo "==> Installing source tarball into rpmbuild"


mkdir -p ~/rpmbuild/SOURCES ~/rpmbuild/SPECS
cp "$PKG_DIR/$NAME-$COMPILE_VER.tar.gz" ~/rpmbuild/SOURCES/
cp "$PKG_DIR/$NAME.spec" ~/rpmbuild/SPECS/

echo "==> Building RPM"
rpmbuild -ba ~/rpmbuild/SPECS/$NAME.spec
find ~/rpmbuild/RPMS -name "*.rpm" -exec cp {} "$RES_DIR" \;

echo "==> Done!"