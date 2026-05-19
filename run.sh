#!/bin/bash
# XAU/USD Daily Reporter - Run Script

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

show_help() {
    echo "XAU/USD Daily Reporter"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  test       Test email configuration"
    echo "  now        Send report immediately (one-time)"
    echo "  schedule   Start daily scheduler (Mon-Fri)"
    echo "  docker     Build and run with Docker Compose"
    echo "  stop       Stop the Docker container"
    echo "  logs       View Docker logs"
    echo ""
}

case "${1:-}" in
    test)
        echo -e "${YELLOW}Testing email configuration...${NC}"
        python -m app.main test
        ;;
    now)
        echo -e "${GREEN}Generating and sending report now...${NC}"
        python -m app.main run
        ;;
    schedule)
        echo -e "${GREEN}Starting daily scheduler...${NC}"
        echo "Reports will be sent Monday-Friday at the configured time."
        echo "Press Ctrl+C to stop."
        echo ""
        python -m app.main schedule
        ;;
    docker)
        echo -e "${GREEN}Building and starting Docker container...${NC}"
        docker-compose up -d --build
        echo -e "${GREEN}Container started!${NC}"
        echo "View logs: ./run.sh logs"
        echo "Stop: ./run.sh stop"
        ;;
    stop)
        echo -e "${YELLOW}Stopping Docker container...${NC}"
        docker-compose down
        ;;
    logs)
        docker-compose logs -f
        ;;
    *)
        show_help
        ;;
esac
