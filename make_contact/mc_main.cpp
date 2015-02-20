#include "mc_main.h"
#include "ui_mc_main.h"

mc_main::mc_main(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::mc_main)
{
    ui->setupUi(this);
}

mc_main::~mc_main()
{
    delete ui;
}
