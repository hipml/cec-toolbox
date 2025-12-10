install:
	install -Dm755 cec-toolbox /usr/bin/cec-toolbox
	install -Dm644 cec-toolbox-suspend.service /usr/lib/systemd/system/cec-toolbox-suspend.service
	install -Dm644 cec-toolbox-wakeup.service /usr/lib/systemd/system/cec-toolbox-wakeup.service

remove:
	rm /usr/bin/cec-toolbox
	rm /usr/lib/systemd/system/cec-toolbox-*
