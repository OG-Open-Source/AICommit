package main

import (
	"log"

	"github.com/OG-Open-Source/aicommit/internal/ui"
)

func main() {
	app, err := ui.NewApplication()
	if err != nil {
		log.Fatalf("無法啟動應用程序: %v", err)
	}
	
	app.Run()
} 