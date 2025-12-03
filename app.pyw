import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance, ImageOps
import os
import glob
import copy
import math

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")  # Can be "Dark", "Light", or "System"
ctk.set_default_color_theme("blue")

class WatermarkLayer:
    """Class to represent a single watermark layer (Text or Image)."""
    def __init__(self, type, content, x=100, y=100, width=300):
        self.id = id(self)  # Unique ID for selection
        self.type = type
        self.content = content  # Text string or PIL Image object (for image layer)
        self.x = x  # Image X coordinate
        self.y = y  # Image Y coordinate
        self.width = width  # Bounding box width for wrapping/resizing
        self.height = 100  # Updated during rendering
        self.opacity = 1.0
        self.rotation = 0  # Add rotation property
        self.aspect_ratio = 1.0  # For image layers
        
        # Text specific
        self.font_path = "arial.ttf" 
        self.font_size = 50
        self.text_color = "#FFFFFF"
        self.align = "center" 
        self.is_bold = False
        self.is_italic = False
        self.line_height = 1.2
        
        # UI State
        self.is_expanded = True
        
        # Store original image for image layers
        if type == 'image' and isinstance(content, Image.Image):
            self.original_image = content.copy()
            self.aspect_ratio = content.height / content.width
            
    def get_font(self):
        """Loads font with proper style handling."""
        try:
            font_path = self.font_path if self.font_path else "arial.ttf"
            font_size = int(self.font_size)
            
            # Try to load the font with proper style
            try:
                # First try to load with style if specified
                if self.is_bold and self.is_italic:
                    # Try to find bold italic variant
                    try:
                        return ImageFont.truetype(font_path, font_size, encoding="unic")
                    except:
                        # Fallback to regular font
                        font = ImageFont.truetype(font_path, font_size)
                        return font
                elif self.is_bold:
                    try:
                        # Try common bold font names
                        bold_path = font_path.replace(".ttf", "bd.ttf").replace(".otf", "bold.otf")
                        return ImageFont.truetype(bold_path, font_size)
                    except:
                        # Fallback to regular with size increase for bold effect
                        font = ImageFont.truetype(font_path, font_size)
                        return font
                elif self.is_italic:
                    try:
                        # Try common italic font names
                        italic_path = font_path.replace(".ttf", "i.ttf").replace(".otf", "italic.otf")
                        return ImageFont.truetype(italic_path, font_size)
                    except:
                        font = ImageFont.truetype(font_path, font_size)
                        return font
                else:
                    return ImageFont.truetype(font_path, font_size)
            except Exception as e:
                # Fallback to default font
                print(f"Font loading error: {e}")
                return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    def get_render_image(self):
        """Generates the transformed PIL Image for this layer."""
        if self.type == 'text':
            font = self.get_font()
            
            # 1. Text Wrapping
            lines = []
            words = self.content.split()
            dummy_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
            max_w_px = int(self.width)
            
            current_line = []
            for word in words:
                test_line = " ".join(current_line + [word])
                bbox = dummy_draw.textbbox((0, 0), test_line, font=font)
                current_w = bbox[2] - bbox[0]
                
                if current_w > max_w_px and current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)
            if current_line:
                lines.append(" ".join(current_line))
            
            # 2. Canvas Size & Draw
            line_height_px = int(self.font_size * self.line_height)
            total_h = len(lines) * line_height_px
            
            img_w = max_w_px + 20 
            img_h = max(total_h, 1) + 20
            
            img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            y_offset = 10
            for line in lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                w_line = line_bbox[2] - line_bbox[0]
                
                # Apply Alignment
                x_pos = 10 
                if self.align == 'center': 
                    x_pos = (img_w - w_line) // 2
                elif self.align == 'right': 
                    x_pos = img_w - w_line - 10
                
                draw.text((x_pos, y_offset), line, font=font, fill=self.text_color)
                y_offset += line_height_px
            
            self.width = img_w
            self.height = img_h

        elif self.type == 'image':
            if not self.content: 
                img = Image.new('RGBA', (100, 100), (255, 0, 0, 128))
                self.width = 100
                self.height = 100
            else:
                # Use original image to maintain quality
                img = self.original_image.copy().convert("RGBA")
                
                # Resize based on stored width while maintaining aspect ratio
                ratio = img.height / img.width
                new_w = int(self.width)
                new_h = int(new_w * ratio)
                
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                self.height = new_h
                self.width = new_w
                self.aspect_ratio = ratio
        
        # Apply Global Opacity
        if self.opacity < 1.0:
            alpha = img.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(self.opacity)
            img.putalpha(alpha)
            
        # Apply rotation if needed
        if self.rotation != 0:
            img = img.rotate(self.rotation, expand=True, resample=Image.BICUBIC)
            
        return img


class WatermarkStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Watermark Studio Pro")
        self.geometry("1400x900")
        
        # --- STATE ---
        self.layers = []
        self.selected_layer_index = None
        self.drag_data = {"mode": None, "start_x": 0, "start_y": 0, "item_start_x": 0, "item_start_y": 0}
        self.resize_direction = None 
        
        # Image Handling
        self.image_files = []
        self.current_image_index = 0
        self.bg_image_pil = None
        self.bg_image_tk = None
        
        # Inline Text Editor state
        self.text_widget = None
        
        # Font Loader
        self.fonts = self.load_fonts()
        
        # Theme tracking
        self.current_mode = "Dark"
        
        self.setup_ui()
        self.create_dummy_bg()

    # --- SETUP & INITIALIZATION ---
    
    def load_fonts(self):
        font_dir = os.path.join(os.path.dirname(__file__), "fonts")
        if not os.path.exists(font_dir): 
            os.makedirs(font_dir)
            
        files = glob.glob(os.path.join(font_dir, "*.[ot]tf"))
        files += glob.glob(os.path.join(font_dir, "*.TTF"))
        files += glob.glob(os.path.join(font_dir, "*.OTF"))
        
        font_map = {}
        for f in files:
            font_name = os.path.splitext(os.path.basename(f))[0]
            font_map[font_name] = f
            
        # Add system fonts
        try:
            # Try to add Arial
            font_map["Arial"] = "arial.ttf"
            font_map["Arial Bold"] = "arialbd.ttf"
            font_map["Arial Italic"] = "ariali.ttf"
        except:
            pass
            
        if not font_map: 
            font_map["Default"] = ""
            
        return font_map

    def setup_ui(self):
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, minsize=300)
        self.grid_rowconfigure(0, weight=1)
        
        self.setup_sidebar()
        self.setup_canvas()
        self.setup_layers_panel()

    def setup_sidebar(self):
        # --- LEFT SIDEBAR (Controls) ---
        self.sidebar = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="#20242e")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Theme switcher
        ctk.CTkLabel(self.sidebar, text="THEME", font=("Arial", 12, "bold"), text_color="#5fa2d8").pack(pady=(20, 5))
        self.theme_switch = ctk.CTkSwitch(self.sidebar, text="Dark Mode", command=self.toggle_theme)
        self.theme_switch.pack(fill="x", padx=20, pady=5)
        self.theme_switch.select()  # Start with dark mode
        
        # Section 1: Folder & Batch
        ctk.CTkLabel(self.sidebar, text="FOLDER & BATCH", font=("Arial", 12, "bold"), text_color="#5fa2d8").pack(pady=(20, 5))
        ctk.CTkButton(self.sidebar, text="📂 Select Image Folder", command=self.select_folder).pack(fill="x", padx=20, pady=5)
        self.folder_status = ctk.CTkLabel(self.sidebar, text="No folder selected.", wraplength=250)
        self.folder_status.pack(fill="x", padx=20, pady=5)

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=10)
        self.prev_btn = ctk.CTkButton(nav_frame, text="< Previous", command=lambda: self.navigate(-1), state="disabled")
        self.prev_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.next_btn = ctk.CTkButton(nav_frame, text="Next >", command=lambda: self.navigate(1), state="disabled")
        self.next_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))
        
        ctk.CTkButton(self.sidebar, text="⚡ BATCH WATERMARK", fg_color="green", hover_color="darkgreen", command=self.start_batch_process).pack(fill="x", padx=20, pady=20)
        
        # Separator
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#3d4659").pack(fill="x", padx=20, pady=10)
        
        # Section 2: Layer Properties
        self.prop_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.prop_frame.pack(fill="x")
        self.prop_frame.columnconfigure(0, weight=1)
        self.prop_frame.columnconfigure(1, weight=1)
        
        self.text_input_label = ctk.CTkLabel(self.prop_frame, text="LAYER CONTENT", font=("Arial", 12, "bold"), text_color="#5fa2d8")
        self.text_input = ctk.CTkEntry(self.prop_frame, height=40, fg_color="#2b3240", border_color="#363d4d")
        self.text_input.bind("<KeyRelease>", self.update_content_live)

        self.font_var = ctk.StringVar(value=list(self.fonts.keys())[0] if self.fonts else "Default")
        self.font_combo = ctk.CTkComboBox(self.prop_frame, values=list(self.fonts.keys()), variable=self.font_var, height=40, fg_color="#2b3240", border_color="#363d4d", command=self.update_font_preview)
        
        # Font preview
        self.font_preview_label = ctk.CTkLabel(self.prop_frame, text="Font Preview: AaBbCc", font=("Arial", 12))
        self.font_preview_label.pack_forget()  # Will be shown when needed
        
        # Toolbar (Align | Bold/Italic)
        self.tool_frame = ctk.CTkFrame(self.prop_frame, fg_color="transparent")
        self.align_var = ctk.StringVar(value="center")
        
        # Create alignment buttons
        self.btn_left = ctk.CTkButton(self.tool_frame, text="L", width=30, height=30, fg_color="#2b3240", hover_color="#363d4d", command=lambda: self.set_align("left"))
        self.btn_left.grid(row=0, column=0, padx=2)
        
        self.btn_center = ctk.CTkButton(self.tool_frame, text="C", width=30, height=30, fg_color="#2b3240", hover_color="#363d4d", command=lambda: self.set_align("center"))
        self.btn_center.grid(row=0, column=1, padx=2)
        
        self.btn_right = ctk.CTkButton(self.tool_frame, text="R", width=30, height=30, fg_color="#2b3240", hover_color="#363d4d", command=lambda: self.set_align("right"))
        self.btn_right.grid(row=0, column=2, padx=2)
        
        ctk.CTkFrame(self.tool_frame, width=2, height=20, fg_color="gray").grid(row=0, column=3, padx=10)
        
        self.is_bold_var = ctk.BooleanVar()
        self.btn_bold = ctk.CTkCheckBox(self.tool_frame, text="B", width=30, variable=self.is_bold_var, command=self.update_style, font=("Arial", 14, "bold"))
        self.btn_bold.grid(row=0, column=4)
        
        self.is_italic_var = ctk.BooleanVar()
        self.btn_italic = ctk.CTkCheckBox(self.tool_frame, text="I", width=30, variable=self.is_italic_var, command=self.update_style, font=("Arial", 14, "italic"))
        self.btn_italic.grid(row=0, column=5)
        
        # Color Picker Button
        self.color_btn = ctk.CTkButton(self.prop_frame, text="🎨 Select Color", command=self.pick_color)
        
        # Size and Opacity
        self.size_slider = self.create_slider(self.prop_frame, "SIZE (Font/Width)", 10, 500, step=5)
        self.opacity_slider = self.create_slider(self.prop_frame, "OPACITY", 0, 1, step=0.01)
        
        # Line Height for text
        self.line_height_slider = self.create_slider(self.prop_frame, "LINE HEIGHT", 0.8, 2.0, step=0.1)
        
        # Rotation slider
        self.rotation_slider = self.create_slider(self.prop_frame, "ROTATION", -180, 180, step=1)

        # Initially hide properties until a layer is selected
        self.set_property_visibility(False)

    def setup_canvas(self):
        # --- CENTER CANVAS (Image Preview) ---
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.canvas_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # For zoom/rotate
        
        # Double click for text editing
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

    def setup_layers_panel(self):
        # --- RIGHT PANEL (Layer List) ---
        self.layer_panel = ctk.CTkFrame(self, corner_radius=0, fg_color="#20242e")
        self.layer_panel.grid(row=0, column=2, sticky="nsew")
        
        ctk.CTkLabel(self.layer_panel, text="LAYERS", font=("Arial", 12, "bold"), text_color="#5fa2d8").pack(pady=(20, 5))
        
        # Layer Creation Buttons
        add_frame = ctk.CTkFrame(self.layer_panel, fg_color="transparent")
        add_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(add_frame, text="+ Text", command=self.add_text_layer).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(add_frame, text="+ Image", command=self.add_image_layer).pack(side="right", expand=True, fill="x", padx=(5, 0))
        
        # Layer reordering buttons
        order_frame = ctk.CTkFrame(self.layer_panel, fg_color="transparent")
        order_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(order_frame, text="↑ Move Up", command=self.move_layer_up).pack(side="left", expand=True, fill="x", padx=(0, 2))
        ctk.CTkButton(order_frame, text="↓ Move Down", command=self.move_layer_down).pack(side="right", expand=True, fill="x", padx=(2, 0))

        self.layer_list_frame = ctk.CTkScrollableFrame(self.layer_panel, fg_color="#20242e")
        self.layer_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_layer_list()

    def create_slider(self, parent, label, from_val, to_val, step=1):
        """Helper to create a labeled slider group."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(frame, text=label, font=("Arial", 10)).pack(anchor="w", padx=0, pady=(10,0))
        slider = ctk.CTkSlider(frame, from_=from_val, to=to_val, number_of_steps=int((to_val - from_val) / step), command=self.update_style)
        slider.set(from_val)
        
        # Value label
        value_label = ctk.CTkLabel(frame, text=f"{from_val}")
        value_label.pack(anchor="e", padx=5, pady=(0,5))
        
        # Update label when slider moves
        def update_label(val):
            value_label.configure(text=f"{float(val):.2f}")
        
        slider.configure(command=lambda val: (update_label(val), self.update_style(val)))
        
        return frame, slider, value_label

    def set_property_visibility(self, visible, layer_type=None):
        """Manages the visibility of the sidebar property controls."""
        
        # Hide all children of the property frame first
        for widget in self.prop_frame.winfo_children():
            widget.pack_forget()

        if not visible:
            ctk.CTkLabel(self.prop_frame, text="Select a layer to edit properties.", text_color="gray").pack(padx=20, pady=40)
            return

        # Common properties
        self.opacity_slider[0].pack(fill="x", padx=20, pady=5)
        self.opacity_slider[1].set(self.layers[self.selected_layer_index].opacity)
        self.rotation_slider[0].pack(fill="x", padx=20, pady=5)
        self.rotation_slider[1].set(self.layers[self.selected_layer_index].rotation)
        
        if layer_type == 'text':
            # Text specific properties
            self.text_input_label.pack(pady=(10, 5))
            self.text_input.pack(fill="x", padx=20, pady=5)
            
            # Font selection with preview
            self.font_combo.pack(fill="x", padx=20, pady=5)
            self.font_preview_label.pack(fill="x", padx=20, pady=(0, 10))
            self.update_font_preview()  # Update preview text
            
            self.tool_frame.pack(fill="x", padx=20, pady=10)
            self.color_btn.pack(fill="x", padx=20, pady=5)
            
            self.size_slider[0].pack(fill="x", padx=20, pady=5)
            self.size_slider[1].set(self.layers[self.selected_layer_index].font_size)
            
            self.line_height_slider[0].pack(fill="x", padx=20, pady=5)
            self.line_height_slider[1].set(self.layers[self.selected_layer_index].line_height)
            
        elif layer_type == 'image':
            # Image specific properties
            ctk.CTkLabel(self.prop_frame, text="IMAGE WIDTH", font=("Arial", 12, "bold"), text_color="#5fa2d8").pack(pady=(10, 5))
            self.size_slider[0].pack(fill="x", padx=20, pady=5)
            self.size_slider[1].set(self.layers[self.selected_layer_index].width)

    # --- THEME MANAGEMENT ---
    
    def toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("Dark")
            self.current_mode = "Dark"
            self.canvas.configure(bg="#1a1a1a")
            self.canvas_frame.configure(fg_color="#1a1a1a")
        else:
            ctk.set_appearance_mode("Light")
            self.current_mode = "Light"
            self.canvas.configure(bg="#f0f0f0")
            self.canvas_frame.configure(fg_color="#f0f0f0")
        self.redraw()

    # --- IMAGE NAVIGATION & BATCH PROCESSING ---
    
    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.image_files = sorted(glob.glob(os.path.join(folder_path, "*.jpg")) + 
                                      glob.glob(os.path.join(folder_path, "*.jpeg")) +
                                      glob.glob(os.path.join(folder_path, "*.png")) +
                                      glob.glob(os.path.join(folder_path, "*.bmp")) +
                                      glob.glob(os.path.join(folder_path, "*.gif")))
            if not self.image_files:
                messagebox.showwarning("Warning", "No image files found.")
                return
            self.current_image_index = 0
            self.load_current_image()
            self.prev_btn.configure(state="normal")
            self.next_btn.configure(state="normal")
    
    def create_dummy_bg(self):
        img = Image.new("RGB", (800, 600), (30, 30, 30))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        draw.text((100, 280), "SELECT FOLDER TO BEGIN", fill="white", font=font)
        self.bg_image_pil = img
        self.redraw()

    def load_current_image(self):
        if not self.image_files: 
            return
        fpath = self.image_files[self.current_image_index]
        try:
            self.bg_image_pil = Image.open(fpath).convert("RGB")
            self.redraw()
            
            # Update navigation buttons state
            self.prev_btn.configure(state="normal" if self.current_image_index > 0 else "disabled")
            self.next_btn.configure(state="normal" if self.current_image_index < len(self.image_files) - 1 else "disabled")
            self.folder_status.configure(text=f"{os.path.basename(fpath)} ({self.current_image_index + 1}/{len(self.image_files)})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def navigate(self, direction):
        if not self.image_files: 
            return
        new_index = self.current_image_index + direction
        if 0 <= new_index < len(self.image_files):
            self.current_image_index = new_index
            self.load_current_image()
            
    def compose_image(self, base_image):
        """Applies all current layers to a base PIL image."""
        base_image = base_image.convert("RGBA")
        for layer in self.layers:
            watermark = layer.get_render_image()
            base_image.paste(watermark, (int(layer.x), int(layer.y)), watermark)
        return base_image.convert("RGB")

    def start_batch_process(self):
        if not self.image_files:
            messagebox.showwarning("Warning", "Please select an image folder first.")
            return

        out_dir = filedialog.askdirectory(title="Select Output Folder")
        if not out_dir: 
            return

        warning = (f"You are about to apply the current watermark design to all {len(self.image_files)} images. "
                   f"Output will be saved to: {out_dir}\n\nDo you wish to proceed?")
        if not messagebox.askyesno("Confirmation", warning): 
            return

        # Create progress window
        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Processing...")
        progress_window.geometry("300x150")
        progress_window.transient(self)
        progress_window.grab_set()
        
        progress_label = ctk.CTkLabel(progress_window, text="Processing images...")
        progress_label.pack(pady=20)
        
        progress_bar = ctk.CTkProgressBar(progress_window, width=250)
        progress_bar.pack(pady=20)
        progress_bar.set(0)
        
        self.update()
        
        total = len(self.image_files)
        processed = 0
        
        for i, fpath in enumerate(self.image_files):
            try:
                base = Image.open(fpath)
                final = self.compose_image(base)
                fname = os.path.basename(fpath)
                save_path = os.path.join(out_dir, "wm_" + fname)
                final.save(save_path, quality=95)
                processed += 1
            except Exception as e:
                print(f"Failed on {fpath}: {e}")
            
            progress_bar.set((i + 1) / total)
            progress_label.configure(text=f"Processed {i + 1}/{total} images")
            self.update()
        
        progress_window.destroy()
        messagebox.showinfo("Complete", f"Successfully processed {processed}/{total} images.")

    # --- LAYER MANAGEMENT ---
    
    def add_text_layer(self):
        if self.bg_image_pil is None:
            messagebox.showwarning("Warning", "Please load an image first.")
            return
            
        new_layer = WatermarkLayer('text', "New Text Watermark")
        new_layer.x = self.bg_image_pil.width * 0.2
        new_layer.y = self.bg_image_pil.height * 0.2
        
        # Set default font
        if self.fonts:
            new_layer.font_path = list(self.fonts.values())[0]
            
        self.layers.append(new_layer)
        self.select_layer(len(self.layers) - 1)
        self.refresh_layer_list()

    def add_image_layer(self):
        if self.bg_image_pil is None:
            messagebox.showwarning("Warning", "Please load an image first.")
            return
            
        path = filedialog.askopenfilename(
            title="Select Image Watermark", 
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("All files", "*.*")
            ]
        )
        if path:
            try:
                img = Image.open(path).convert("RGBA")
                new_layer = WatermarkLayer('image', img)
                new_layer.width = min(300, img.width)  # Default size
                new_layer.x = self.bg_image_pil.width * 0.3
                new_layer.y = self.bg_image_pil.height * 0.3
                self.layers.append(new_layer)
                self.select_layer(len(self.layers) - 1)
                self.refresh_layer_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def delete_layer(self, index):
        if 0 <= index < len(self.layers):
            self.layers.pop(index)
            if self.selected_layer_index == index:
                self.selected_layer_index = None
                self.set_property_visibility(False)
            elif self.selected_layer_index > index:
                self.selected_layer_index -= 1
            self.refresh_layer_list()
            self.redraw()

    def select_layer(self, index):
        if 0 <= index < len(self.layers):
            self.selected_layer_index = index
            layer = self.layers[index]
            self.refresh_layer_list()
            self.set_property_visibility(True, layer.type)
            if layer.type == 'text':
                self.refresh_text_controls(layer)
            elif layer.type == 'image':
                self.refresh_image_controls(layer)
            self.redraw()
            
    def move_layer_up(self):
        if self.selected_layer_index is not None and self.selected_layer_index > 0:
            # Swap layers
            self.layers[self.selected_layer_index], self.layers[self.selected_layer_index - 1] = \
                self.layers[self.selected_layer_index - 1], self.layers[self.selected_layer_index]
            self.selected_layer_index -= 1
            self.refresh_layer_list()
            self.redraw()
            
    def move_layer_down(self):
        if self.selected_layer_index is not None and self.selected_layer_index < len(self.layers) - 1:
            # Swap layers
            self.layers[self.selected_layer_index], self.layers[self.selected_layer_index + 1] = \
                self.layers[self.selected_layer_index + 1], self.layers[self.selected_layer_index]
            self.selected_layer_index += 1
            self.refresh_layer_list()
            self.redraw()
            
    def refresh_text_controls(self, layer):
        self.text_input.delete(0, "end")
        self.text_input.insert(0, layer.content)
        self.size_slider[1].set(layer.font_size)
        self.opacity_slider[1].set(layer.opacity)
        self.rotation_slider[1].set(layer.rotation)
        self.is_bold_var.set(layer.is_bold)
        self.is_italic_var.set(layer.is_italic)
        self.line_height_slider[1].set(layer.line_height)
        self.set_align(layer.align)
        
        # Find and set the font in combobox
        for name, path in self.fonts.items():
            if path == layer.font_path:
                self.font_var.set(name)
                break
        else:
            # If not found, try to match by filename
            for name, path in self.fonts.items():
                if os.path.basename(path) == os.path.basename(layer.font_path):
                    self.font_var.set(name)
                    break
        
    def refresh_image_controls(self, layer):
        self.size_slider[1].set(layer.width)
        self.opacity_slider[1].set(layer.opacity)
        self.rotation_slider[1].set(layer.rotation)
        
    def toggle_layer_expand(self, index):
        if 0 <= index < len(self.layers):
            self.layers[index].is_expanded = not self.layers[index].is_expanded
            self.refresh_layer_list()

    def refresh_layer_list(self):
        # Clear previous list
        for widget in self.layer_list_frame.winfo_children():
            widget.destroy()
            
        for i, layer in reversed(list(enumerate(self.layers))):
            is_selected = i == self.selected_layer_index
            
            # --- Header Frame (Always visible) ---
            header_frame = ctk.CTkFrame(self.layer_list_frame, 
                                       fg_color="#3d4659" if is_selected else "#2b3240", 
                                       border_color="#3b82f6" if is_selected else "transparent", 
                                       border_width=2 if is_selected else 0)
            header_frame.pack(fill="x", pady=2)
            
            # Expand/Contract Button
            arrow_icon = "▼" if layer.is_expanded else "►"
            expand_btn = ctk.CTkButton(header_frame, text=arrow_icon, width=20, 
                                       fg_color="transparent", hover_color="#4a556b", 
                                       command=lambda idx=i: self.toggle_layer_expand(idx))
            expand_btn.pack(side="left", padx=5)
            
            # Label with layer info
            if layer.type == 'text':
                content_preview = layer.content[:20] + "..." if len(layer.content) > 20 else layer.content
                label_text = f"📝 {content_preview}"
            else:
                label_text = f"🖼 Image ({layer.width}x{layer.height})"
                
            label = ctk.CTkLabel(header_frame, text=label_text, anchor="w")
            label.pack(side="left", padx=5, pady=5, expand=True)
            
            # Select button
            select_btn = ctk.CTkButton(header_frame, text="Select", width=60, 
                                       command=lambda idx=i: self.select_layer(idx))
            select_btn.pack(side="right", padx=5)
            
            # Delete button
            delete_btn = ctk.CTkButton(header_frame, text="🗑", width=30, 
                                       fg_color="red", hover_color="darkred", 
                                       command=lambda idx=i: self.delete_layer(idx))
            delete_btn.pack(side="right", padx=5)

            # --- Expanded Details (Only visible if expanded) ---
            if layer.is_expanded:
                detail_frame = ctk.CTkFrame(self.layer_list_frame, fg_color="#2b3240")
                detail_frame.pack(fill="x", pady=(0, 5))
                
                # Position info
                pos_frame = ctk.CTkFrame(detail_frame, fg_color="transparent")
                pos_frame.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(pos_frame, text=f"X: {int(layer.x)}", width=60).pack(side="left")
                ctk.CTkLabel(pos_frame, text=f"Y: {int(layer.y)}", width=60).pack(side="left", padx=10)
                
                # Size info
                size_frame = ctk.CTkFrame(detail_frame, fg_color="transparent")
                size_frame.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(size_frame, text=f"W: {int(layer.width)}", width=60).pack(side="left")
                ctk.CTkLabel(size_frame, text=f"H: {int(layer.height)}", width=60).pack(side="left", padx=10)
                
                # Opacity info
                ctk.CTkLabel(detail_frame, text=f"Opacity: {layer.opacity:.2f}", anchor="w").pack(fill="x", padx=10, pady=5)
                
                # Rotation info
                ctk.CTkLabel(detail_frame, text=f"Rotation: {layer.rotation}°", anchor="w").pack(fill="x", padx=10, pady=5)

    def pick_color(self):
        """Opens a native color wheel/picker dialog."""
        if self.selected_layer_index is not None:
            layer = self.layers[self.selected_layer_index]
            if layer.type == 'text':
                # Open color chooser with current color
                color_code = colorchooser.askcolor(
                    title="Select Text Color", 
                    color=layer.text_color,
                    parent=self
                )
                if color_code[1]:  # User didn't cancel
                    hex_color = color_code[1]
                    layer.text_color = hex_color
                    # Update button color
                    self.color_btn.configure(fg_color=hex_color)
                    self.redraw()

    def set_align(self, mode):
        self.align_var.set(mode)
        # Update button states
        self.btn_left.configure(fg_color="#3b82f6" if mode == "left" else "#2b3240")
        self.btn_center.configure(fg_color="#3b82f6" if mode == "center" else "#2b3240")
        self.btn_right.configure(fg_color="#3b82f6" if mode == "right" else "#2b3240")
        self.update_style()
        
    def update_font_preview(self, event=None):
        """Update font preview when font is selected."""
        selected_font = self.font_var.get()
        if selected_font in self.fonts:
            # Update font preview label with selected font name
            self.font_preview_label.configure(text=f"Preview: {selected_font}")
            
            # Update the selected layer's font
            if self.selected_layer_index is not None:
                layer = self.layers[self.selected_layer_index]
                if layer.type == 'text':
                    layer.font_path = self.fonts[selected_font]
                    self.redraw()
    
    def update_content_live(self, event):
        if self.selected_layer_index is not None:
            layer = self.layers[self.selected_layer_index]
            if layer.type == 'text':
                layer.content = self.text_input.get()
                self.redraw()
    
    def update_style(self, val=None):
        if self.selected_layer_index is not None:
            l = self.layers[self.selected_layer_index]
            
            if l.type == 'text':
                l.font_size = self.size_slider[1].get()
                l.align = self.align_var.get()
                l.is_bold = self.is_bold_var.get()
                l.is_italic = self.is_italic_var.get()
                l.line_height = self.line_height_slider[1].get()
                # Font path is updated in update_font_preview
            elif l.type == 'image':
                l.width = self.size_slider[1].get()
                
            l.opacity = self.opacity_slider[1].get()
            l.rotation = self.rotation_slider[1].get()
            self.redraw()

    # --- CANVAS RENDERING ---

    def redraw(self):
        self.canvas.delete("all")
        if not self.bg_image_pil: 
            return
        
        c_w = self.canvas.winfo_width()
        c_h = self.canvas.winfo_height()
        
        if c_w <= 1 or c_h <= 1:  # Canvas not ready
            return
            
        img_ratio = self.bg_image_pil.width / self.bg_image_pil.height
        c_ratio = c_w / c_h
        
        # Calculate fit
        if img_ratio > c_ratio:
            disp_w = c_w
            disp_h = int(c_w / img_ratio)
        else:
            disp_h = c_h
            disp_w = int(c_h * img_ratio)
            
        self.scale_factor = disp_w / self.bg_image_pil.width
        self.offset_x = (c_w - disp_w) // 2
        self.offset_y = (c_h - disp_h) // 2
        
        # Draw Background
        resized = self.bg_image_pil.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        self.bg_image_tk = ImageTk.PhotoImage(resized)
        self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.bg_image_tk)
        
        # Render Layers
        for i, layer in enumerate(self.layers):
            l_img = layer.get_render_image()
            if l_img.size[0] == 0 or l_img.size[1] == 0:
                continue
                
            l_tk = ImageTk.PhotoImage(l_img)
            layer._tk_ref = l_tk  # Keep reference
            
            lx = (layer.x * self.scale_factor) + self.offset_x
            ly = (layer.y * self.scale_factor) + self.offset_y
            
            self.canvas.create_image(lx, ly, anchor="nw", image=l_tk, tags=(f"layer_{i}", "layer_item"))
            
            # Selection Box & Handles
            if i == self.selected_layer_index:
                w = l_img.width
                h = l_img.height
                
                # Selection box
                self.canvas.create_rectangle(lx, ly, lx+w, ly+h, 
                                           outline="#3b82f6", width=2, dash=(4,2), 
                                           tags="selection_box")
                
                # Resizing Handles
                handle_size = 8
                handles = [
                    (lx, ly, "nw"), (lx + w, ly, "ne"),
                    (lx + w, ly + h, "se"), (lx, ly + h, "sw"),
                    (lx + w/2, ly, "n"), (lx + w/2, ly + h, "s"),
                    (lx + w, ly + h/2, "e"), (lx, ly + h/2, "w")
                ]
                
                for hx, hy, tag in handles:
                    self.canvas.create_rectangle(hx - handle_size, hy - handle_size,
                                               hx + handle_size, hy + handle_size,
                                               fill="#3b82f6", outline="white", 
                                               tags=(f"handle_{tag}", "handle"))

    def on_double_click(self, event):
        """Handle double-click on text layer for inline editing."""
        # Check if we clicked on a layer
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("layer_"):
                    layer_idx = int(tag.split("_")[1])
                    if 0 <= layer_idx < len(self.layers):
                        layer = self.layers[layer_idx]
                        if layer.type == 'text':
                            self.select_layer(layer_idx)
                            self.toggle_text_editor()
                            return

    def toggle_text_editor(self):
        """Open inline text editor for selected text layer."""
        if self.selected_layer_index is None:
            return
            
        layer = self.layers[self.selected_layer_index]
        if layer.type != 'text':
            return
            
        # Close existing editor
        if self.text_widget and self.text_widget.winfo_exists():
            self.close_text_editor()
        
        # Get layer position and size
        lx, ly, w, h = self.get_layer_bbox(self.selected_layer_index)
        
        # Create text widget
        self.text_widget = tk.Text(self.canvas, wrap="word", 
                                  bg="#3b3b3b", fg="white",
                                  insertbackground="white",
                                  selectbackground="#3b82f6",
                                  selectforeground="white",
                                  relief="solid", borderwidth=1)
        
        self.text_widget.insert("1.0", layer.content)
        self.text_widget.place(x=lx, y=ly, width=w, height=h)
        self.text_widget.focus_set()
        
        # Select all text
        self.text_widget.tag_add("sel", "1.0", "end")
        
        # Bind events
        self.text_widget.bind("<FocusOut>", lambda e: self.close_text_editor())
        self.text_widget.bind("<Control-s>", lambda e: self.close_text_editor())
        self.text_widget.bind("<Escape>", lambda e: self.close_text_editor())

    def close_text_editor(self, event=None):
        """Close the inline text editor and save changes."""
        if self.text_widget and self.text_widget.winfo_exists():
            new_content = self.text_widget.get("1.0", "end-1c")
            if self.selected_layer_index is not None:
                self.layers[self.selected_layer_index].content = new_content
                self.refresh_text_controls(self.layers[self.selected_layer_index])
                self.redraw()
            self.text_widget.place_forget()
            self.text_widget = None

    # --- DRAG & RESIZE LOGIC ---

    def get_layer_bbox(self, index):
        """Returns layer's position and dimensions in CANVAS coordinates."""
        if index < 0 or index >= len(self.layers):
            return 0, 0, 0, 0
            
        l = self.layers[index]
        l_img = l.get_render_image()
        w = l_img.width
        h = l_img.height
        lx = (l.x * self.scale_factor) + self.offset_x
        ly = (l.y * self.scale_factor) + self.offset_y
        return lx, ly, w, h
        
    def on_press(self, event):
        self.drag_data["start_x"] = event.x
        self.drag_data["start_y"] = event.y
        self.drag_data["mode"] = None
        self.resize_direction = None
        
        # Close text editor if open
        if self.text_widget and self.text_widget.winfo_exists():
            self.close_text_editor()
        
        # 1. Check for Handle Hit (Resize)
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("handle_"):
                    self.resize_direction = tag.split("_")[1]
                    self.drag_data["mode"] = "resize"
                    if self.selected_layer_index is not None:
                        l = self.layers[self.selected_layer_index]
                        self.drag_data["item_start_x"] = l.x
                        self.drag_data["item_start_y"] = l.y
                        self.drag_data["item_start_w"] = l.width
                        self.drag_data["item_start_h"] = l.height
                    return

        # 2. Check for Layer Hit (Move)
        for i in reversed(range(len(self.layers))):
            lx, ly, w, h = self.get_layer_bbox(i)
            if lx <= event.x <= lx + w and ly <= event.y <= ly + h:
                self.select_layer(i)
                self.drag_data["mode"] = "move"
                self.drag_data["item_start_x"] = self.layers[i].x
                self.drag_data["item_start_y"] = self.layers[i].y
                return
        
        # Deselect if no hit
        self.selected_layer_index = None
        self.redraw()
        self.set_property_visibility(False)

    def on_drag(self, event):
        if self.drag_data["mode"] is None or self.selected_layer_index is None:
            return
        
        dx_screen = event.x - self.drag_data["start_x"]
        dy_screen = event.y - self.drag_data["start_y"]
        l = self.layers[self.selected_layer_index]

        dx_img = dx_screen / self.scale_factor
        dy_img = dy_screen / self.scale_factor

        if self.drag_data["mode"] == "move":
            l.x = self.drag_data["item_start_x"] + dx_img
            l.y = self.drag_data["item_start_y"] + dy_img

        elif self.drag_data["mode"] == "resize":
            start_x_img = self.drag_data["item_start_x"]
            start_y_img = self.drag_data["item_start_y"]
            start_w_img = self.drag_data["item_start_w"]
            
            # Calculate new width based on resize direction
            if 'e' in self.resize_direction:
                l.width = max(20, start_w_img + dx_img)
            if 'w' in self.resize_direction:
                new_w = max(20, start_w_img - dx_img)
                l.x = start_x_img + dx_img
                l.width = new_w
            
            # Adjust Y position for north resizing
            if 'n' in self.resize_direction:
                l.y = start_y_img + dy_img
                
            # For image layers, maintain aspect ratio if shift is held
            if l.type == 'image' and event.state & 0x1:  # Shift key
                ratio = l.aspect_ratio
                l.height = l.width * ratio
                
            if l.type == 'text':
                self.size_slider[1].set(l.font_size)
            elif l.type == 'image':
                self.size_slider[1].set(l.width)
                 
        self.redraw()

    def on_release(self, event):
        self.drag_data["mode"] = None
        self.refresh_layer_list()
        
    def on_mousewheel(self, event):
        """Handle mouse wheel for zoom or rotation."""
        if self.selected_layer_index is not None and event.state & 0x4:  # Control key
            layer = self.layers[self.selected_layer_index]
            # Adjust rotation
            layer.rotation += 1 if event.delta > 0 else -1
            layer.rotation %= 360
            self.rotation_slider[1].set(layer.rotation)
            self.redraw()
        elif event.state & 0x1:  # Shift key - adjust opacity
            if self.selected_layer_index is not None:
                layer = self.layers[self.selected_layer_index]
                layer.opacity += 0.05 if event.delta > 0 else -0.05
                layer.opacity = max(0.0, min(1.0, layer.opacity))
                self.opacity_slider[1].set(layer.opacity)
                self.redraw()


if __name__ == "__main__":
    app = WatermarkStudio()
    app.mainloop()