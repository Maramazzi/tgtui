#!/usr/bin/env bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ████████╗ ██████╗ ████████╗██╗   ██╗██╗"
echo "     ██╔══╝██╔════╝    ██╔══╝██║   ██║██║"
echo "     ██║   ██║  ███╗   ██║   ██║   ██║██║"
echo "     ██║   ██║   ██║   ██║   ██║   ██║██║"
echo "     ██║   ╚██████╔╝   ██║   ╚██████╔╝██║"
echo "     ╚═╝    ╚═════╝    ╚═╝    ╚═════╝ ╚═╝"
echo -e "${NC}"
echo -e "${CYAN}Minimalist Telegram TUI Client${NC}"
echo "------------------------------------"

# 1. Проверка Python 3.10+
echo -e "\n${YELLOW}[1/5] Проверка Python...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Ошибка: python3 не найден. Установите Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED="3.10"
if python3 -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
else
    echo -e "${RED}Ошибка: нужен Python 3.10+, найден $PYTHON_VERSION${NC}"
    exit 1
fi

# 2. Создание virtualenv
INSTALL_DIR="$HOME/.local/share/tgtui"
echo -e "\n${YELLOW}[2/5] Создание виртуального окружения в $INSTALL_DIR ...${NC}"
mkdir -p "$INSTALL_DIR"
python3 -m venv "$INSTALL_DIR/venv"
echo -e "${GREEN}✓ Готово${NC}"

# 3. Установка зависимостей
echo -e "\n${YELLOW}[3/5] Установка зависимостей...${NC}"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet -r requirements.txt
echo -e "${GREEN}✓ Зависимости установлены${NC}"

# 4. Конфиг директория
echo -e "\n${YELLOW}[4/5] Создание конфиг директории...${NC}"
mkdir -p "$HOME/.config/tgtui/downloads"
echo -e "${GREEN}✓ ~/.config/tgtui/ готова${NC}"

# 5. Алиас в shell
echo -e "\n${YELLOW}[5/5] Добавление команды tgtui...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$HOME/.local/bin/tgtui"
mkdir -p "$HOME/.local/bin"

cat > "$LAUNCHER" << LAUNCHER_EOF
#!/usr/bin/env bash
"$INSTALL_DIR/venv/bin/python" "$SCRIPT_DIR/main.py" "\$@"
LAUNCHER_EOF
chmod +x "$LAUNCHER"

# Добавляем ~/.local/bin в PATH если ещё нет
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC" ] && ! grep -q 'LOCAL_BIN' "$RC"; then
        echo '' >> "$RC"
        echo '# tgtui' >> "$RC"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
    fi
done

echo -e "${GREEN}✓ Команда tgtui добавлена${NC}"

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Установка завершена!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Следующий шаг — получи API ключи:${NC}"
echo "  1. Открой https://my.telegram.org"
echo "  2. Войди под своим номером телефона"
echo "  3. Перейди в 'API development tools'"
echo "  4. Создай приложение, скопируй api_id и api_hash"
echo ""
echo -e "${CYAN}Запуск:${NC}"
echo "  source ~/.bashrc   # или перезапусти терминал"
echo "  tgtui"
echo ""
