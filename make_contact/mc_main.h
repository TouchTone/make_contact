#ifndef MC_MAIN_H
#define MC_MAIN_H

#include <QMainWindow>

namespace Ui {
class mc_main;
}

class mc_main : public QMainWindow
{
    Q_OBJECT

public:
    explicit mc_main(QWidget *parent = 0);
    ~mc_main();

private:
    Ui::mc_main *ui;
};

#endif // MC_MAIN_H
