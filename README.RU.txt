Установка и запуск ViperPeers

Установка

    * Качаем и ставим: Python (http://www.python.org/download/releases/)
    * Качаем и ставим: PyYaml (http://pyyaml.org/wiki/PyYAML) (соответственно версии питона)
    * Качаем и ставим: Twisted (http://twistedmatrix.com/trac/) (соответственно версии питона)

    Для Debian/Ubuntu вышеуказанные действия можно заменить командой apt-get install python-twisted-core python-yaml

Запуск

    * Запуск в консоли - ./viperpeers.py
    * Запуск в режиме демона - twistd -y viperpeers-app.tac
    * Логинимся на машину с хабой на 411 порт (адрес: localhost если это локальный компьютер) с логином: admin и паролем: megapass
    * Меняем пароль админа
    * :)

Что дальше?
    Для автоматического запуска хаба после перезагрузки системы необходим init-script.
    Для просмотра всех возможностей запуска демона через twistd прочтите man twistd.
