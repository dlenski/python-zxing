#!/bin/sh

dest="$(dirname $0)/zxing/java"
echo "Downloading zxing-javase, zxing-core, and jcommander JARs into $dest ..."

cd "$dest"
[ -s javase.jar ] || wget https://repo1.maven.org/maven2/com/google/zxing/javase/3.3.0/javase-3.3.0.jar -O javase.jar
[ -s core.jar ] || wget https://repo1.maven.org/maven2/com/google/zxing/core/3.3.0/core-3.3.0.jar -O core.jar
[ -s jcommander.jar ] || wget https://repo1.maven.org/maven2/com/beust/jcommander/1.7/jcommander-1.7.jar -O jcommander.jar
