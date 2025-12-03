# 💧 Watermark Studio

A lightweight, fast, and user-friendly watermark editor for batch processing images. No coding knowledge required!

## ✨ Features

- 🖼️ **Batch Processing** - Watermark multiple images at once
- 📁 **Folder Support** - Load entire folders of images
- 🎨 **Text & Image Watermarks** - Add custom text or logo watermarks
- 🔤 **Custom Fonts** - Use your own font files
- ⚡ **Fast & Lightweight** - Minimal resource usage
- 🎯 **WYSIWYG** - What you see is what you export
- 📦 **ZIP Export** - Download all watermarked images in one go
- 🎭 **Full Control** - Position, rotate, resize, adjust opacity

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/official-imvoiid/Watermark-App.git
   cd Watermark-App/Watermark-Studio
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run the application**
   ```bash
   npm run dev
   ```

## 🎨 Adding Custom Fonts

Want to use your own fonts? Follow these steps:

1. **Place your font files** in the `public/fonts/` directory
   - Supported formats: `.ttf`, `.otf`, `.woff`, `.woff2`

2. **Update the font list** in `public/fonts/fonts.json`
   ```json
   [
     "YourFont.ttf",
     "AnotherFont.otf",
     "CustomFont.woff"
   ]
   ```

3. **Restart the app** - Your fonts will appear in the font selector!

### 📝 Font Naming Tips
- Keep filenames simple (no spaces or special characters)
- The app displays the font name without the extension

## 📖 How to Use

### Loading Images
- **Folder** 📁 - Load all images from a folder
- **Image** 🖼️ - Add individual images

### Adding Watermarks
1. Click **T** icon for text watermark or **🖼️** icon for image watermark
2. Customize position, size, rotation, and opacity
3. Drag watermarks on the canvas to reposition

### Batch Copying
Use **"Copy to All Images"** to apply the same watermark settings to all loaded images

### Exporting
Click **"Export ZIP"** to download all watermarked images as a single ZIP file

## ⚠️ Font License Notice

**IMPORTANT:** The fonts included in `public/fonts/` are **for personal use only** and are provided as examples. They are **NOT owned by this project** and remain the property of their respective creators.

### Using Custom Fonts
- ✅ You may use your own licensed fonts
- ✅ Ensure you have the right to use any fonts you add
- ❌ Do not distribute fonts without proper licensing
- ⚖️ Respect font creators' intellectual property

**If you're the font creator and want your font removed, please open an issue.**

## 🛠️ Tech Stack

- **React** + **TypeScript**
- **Vite** - Fast build tool
- **Fabric.js** - Canvas manipulation
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components

## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests

## 📄 License

MIT License - See LICENSE file for details

---

Made with ❤️ for creators who need simple, fast watermarking

**Star ⭐ this repo if you find it useful!**
