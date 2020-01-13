for D in `ls -d automatic_classification_illegal_av__*`
do
    echo '#####' $D
    find $D ! -path $D -type d -maxdepth 1 | xargs rm -rf {}
    rm -rf $D/*.zip
done