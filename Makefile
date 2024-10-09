VENV_DIR := venv
SHORTCUT_DEST := $(HOME)/.local/share/applications/
SHORTCUT := $(wildcard *.desktop)
SHORTCUT_IN_PLACE := $(addprefix $(SHORTCUT_DEST),$(SHORTCUT))



$(VENV_DIR):
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install -r requirements.txt


.PHONY: run-ui
run-ui: $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && ./torque_ui


.PHONY: run-ui-ask
run-ui-ask: $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && ./torque_ui --ask-outfile


.PHONY: update-shortcut
update-shortcut:
	mkdir -p $(SHORTCUT_DEST)
	cp $(SHORTCUT) $(SHORTCUT_DEST)/
	echo chmod +x $(SHORTCUT_IN_PLACE)
	echo sudo update-desktop-database -v $(SHORTCUT_DEST)
	for n in $(SHORTCUT_IN_PLACE); do \
		ln -sf $$n ~/Desktop; \
	done

