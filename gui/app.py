import json
import sys
import traceback
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, TOP, BOTTOM, X, Y, NW, Canvas, StringVar, Tk, Text, filedialog, messagebox
from tkinter import ttk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_pipeline
from src.utils.file_io import save_json

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class DiagramDigitizerApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Control Diagram Digitizer")
        self.root.geometry("1100x720")
        self.root.minsize(900, 620)

        self.selected_image: Path | None = None
        self.output_data: dict | None = None
        self.output_path = PROJECT_ROOT / "data" / "output" / "latest_output.json"
        self.preview_image = None

        self.root.configure(bg="#0d0e18")
        self.style = ttk.Style(root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.setup_styles()

        header = ttk.Frame(root, padding=(18, 16), style="Header.TFrame")
        header.pack(fill=X)

        title = ttk.Label(header, text="Control Diagram Digitizer", style="Header.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(
            header,
            text="Transform control diagrams into structured JSON with a vivid, interactive interface.",
            style="SubHeader.TLabel",
        )
        subtitle.pack(anchor="w", pady=(6, 4))

        action_bar = ttk.Frame(root, padding=(16, 10), style="Card.TFrame")
        action_bar.pack(fill=X, pady=(0, 12))

        self.image_label_var = StringVar(value="No image selected")
        self.image_label = ttk.Label(action_bar, textvariable=self.image_label_var, style="Info.TLabel", anchor="w")
        self.image_label.pack(side=LEFT, fill=X, expand=True)

        self.sample_images = self.load_sample_image_list()
        self.sample_var = StringVar(value="Select sample")
        self.sample_select = ttk.Combobox(
            action_bar,
            textvariable=self.sample_var,
            values=self.sample_images,
            width=24,
            state="readonly",
            justify="center",
            style="Accent.TCombobox",
        )
        if self.sample_images:
            self.sample_select.pack(side=RIGHT, padx=4)

        self.sample_button = ttk.Button(action_bar, text="Load Sample", command=self.load_selected_sample, style="Accent.TButton")
        self.sample_button.pack(side=RIGHT, padx=4)

        self.browse_button = ttk.Button(action_bar, text="Browse Image", command=self.browse_image, style="Accent.TButton")
        self.browse_button.pack(side=RIGHT, padx=4)

        self.run_button = ttk.Button(action_bar, text="Run Pipeline", command=self.run_pipeline_from_gui, style="Accent.TButton")
        self.run_button.pack(side=RIGHT, padx=4)

        self.save_button = ttk.Button(action_bar, text="Save Output As...", command=self.save_output_as, state="disabled", style="Accent.TButton")
        self.save_button.pack(side=RIGHT)

        body = ttk.Frame(root, padding=(16, 0, 16, 12), style="Main.TFrame")
        body.pack(fill=BOTH, expand=True)

        left_pane = ttk.Frame(body)
        left_pane.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

        preview_frame = ttk.LabelFrame(left_pane, text="Image Preview", padding=(10, 10), style="Card.TFrame")
        preview_frame.pack(fill=BOTH, expand=True)

        self.preview_canvas = Canvas(preview_frame, background="#111224", highlightthickness=0)
        self.preview_canvas.pack(fill=BOTH, expand=True)
        self.preview_canvas.create_text(
            16,
            16,
            anchor=NW,
            text="No image loaded. Select an image to preview.",
            fill="#b3b5ff",
            font=("Segoe UI", 10),
            tags="placeholder",
        )

        stats_frame = ttk.Frame(left_pane, style="Card.TFrame", padding=(0, 10, 0, 0))
        stats_frame.pack(fill=X, pady=(10, 0))
        self.stats = {}
        for label_text, key in [("Image", "image"), ("Blocks", "blocks"), ("Text", "text"), ("Connections", "connections")]:
            stat_card = ttk.Frame(stats_frame, style="Card.TFrame", padding=8)
            stat_card.pack(side=LEFT, fill=X, expand=True, padx=4)
            title_label = ttk.Label(stat_card, text=label_text, style="StatHeader.TLabel")
            title_label.pack(anchor="w")
            value_label = ttk.Label(stat_card, text="—", style="StatValue.TLabel")
            value_label.pack(anchor="w", pady=(4, 0))
            self.stats[key] = value_label

        detail_frame = ttk.LabelFrame(left_pane, text="Input Details", padding=(10, 10), style="Card.TFrame")
        detail_frame.pack(fill=X, pady=(10, 0))

        self.details_text = Text(detail_frame, height=6, wrap="word", state="disabled", bg="#111224", fg="#e6e8ff", insertbackground="#ffffff", relief="flat")
        self.details_text.pack(fill=BOTH, expand=True)

        right_pane = ttk.Frame(body)
        right_pane.pack(side=RIGHT, fill=BOTH, expand=True)

        self.notebook = ttk.Notebook(right_pane)
        self.notebook.pack(fill=BOTH, expand=True)

        self.json_frame = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(self.json_frame, text="JSON Output")

        self.json_text = Text(self.json_frame, wrap="none", padx=10, pady=10, state="disabled", bg="#111224", fg="#f4f5ff", insertbackground="#f4f5ff", relief="flat")
        self.json_text.pack(fill=BOTH, expand=True, side=LEFT)

        json_vscroll = ttk.Scrollbar(self.json_frame, orient="vertical", command=self.json_text.yview)
        json_vscroll.pack(fill=Y, side=RIGHT)
        json_hscroll = ttk.Scrollbar(self.json_frame, orient="horizontal", command=self.json_text.xview)
        json_hscroll.pack(fill=X, side=BOTTOM)
        self.json_text.configure(yscrollcommand=json_vscroll.set, xscrollcommand=json_hscroll.set)

        controls_frame = ttk.Frame(self.json_frame, padding=(10, 8, 10, 4), style="Card.TFrame")
        controls_frame.pack(fill=X)

        copy_button = ttk.Button(controls_frame, text="Copy JSON", command=self.copy_json_to_clipboard, style="Accent.TButton")
        copy_button.pack(side=LEFT)

        self.summary_frame = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(self.summary_frame, text="Summary")

        self.summary_text = Text(self.summary_frame, wrap="word", padx=10, pady=10, state="disabled", bg="#111224", fg="#f4f5ff", insertbackground="#f4f5ff", relief="flat")
        self.summary_text.pack(fill=BOTH, expand=True)

        self.log_frame = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(self.log_frame, text="Status Log")

        self.log_text = Text(
            self.log_frame,
            wrap="word",
            padx=10,
            pady=10,
            state="disabled",
            bg="#111224",
            fg="#c3d8ff",
            insertbackground="#ffffff",
        )
        self.log_text.pack(fill=BOTH, expand=True)

        self.progress = ttk.Progressbar(root, mode="determinate", maximum=100, style="Accent.Horizontal.TProgressbar")
        self.progress.pack(fill=X, padx=16, pady=(0, 6))

        self.status_var = StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w", padding=(10, 4), style="Status.TLabel")
        status_bar.pack(fill=X, side=BOTTOM)

        self.log("Application ready.")

    def setup_styles(self) -> None:
        self.style.configure("Header.TFrame", background="#1f1b41")
        self.style.configure("Header.TLabel", background="#1f1b41", foreground="#f8f8ff", font=("Segoe UI", 20, "bold"))
        self.style.configure("SubHeader.TLabel", background="#1f1b41", foreground="#d6d0ff", font=("Segoe UI", 10))

        self.style.configure("Main.TFrame", background="#0d0e18")
        self.style.configure("Card.TFrame", background="#121429")
        self.style.configure("Info.TLabel", background="#121429", foreground="#d4d8ff")
        self.style.configure("Status.TLabel", background="#0a0c14", foreground="#a5c8ff")
        self.style.configure("StatHeader.TLabel", background="#121429", foreground="#a5b8ff", font=("Segoe UI", 9, "bold"))
        self.style.configure("StatValue.TLabel", background="#121429", foreground="#f7f8ff", font=("Segoe UI", 14, "bold"))
        self.style.configure("Accent.TButton", background="#7268ff", foreground="#ffffff", padding=8)
        self.style.configure("Accent.TCombobox", fieldbackground="#121429", background="#121429", foreground="#ffffff")
        self.style.configure("Accent.Horizontal.TProgressbar", troughcolor="#111224", background="#7c6cff")
        self.style.configure("TNotebook", background="#0d0e18", tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab", background="#1f1b41", foreground="#e8d9ff", padding=(14, 8))
        self.style.map("Accent.TButton", background=[("active", "#7e79ff"), ("pressed", "#5d53d6")])

    def load_sample_image_list(self) -> list[str]:
        sample_dir = PROJECT_ROOT / "data" / "sample"
        if not sample_dir.exists():
            return []
        image_files = [p.name for p in sample_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}]
        return sorted(image_files)

    def load_selected_sample(self) -> None:
        if not self.sample_images:
            self.load_sample_image()
            return

        selection = self.sample_var.get()
        if not selection or selection == "Select sample":
            self.load_sample_image()
            return

        sample_image = PROJECT_ROOT / "data" / "sample" / selection
        if sample_image.exists():
            self.set_image(sample_image)
        else:
            messagebox.showwarning("Sample image missing", "The selected sample image could not be found.")

    def log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(END, f"{message}\n")
        self.log_text.see(END)
        self.log_text.configure(state="disabled")

    def update_status(self, message: str, progress_value: int = 0) -> None:
        self.status_var.set(message)
        self.progress["value"] = progress_value
        self.root.update_idletasks()

    def browse_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select diagram image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.set_image(Path(file_path))

    def load_sample_image(self) -> None:
        sample_image = PROJECT_ROOT / "data" / "sample" / "sample_diagram.png"
        if sample_image.exists():
            self.set_image(sample_image)
        else:
            messagebox.showwarning("Sample image missing", "Sample diagram image could not be found.")

    def set_image(self, image_path: Path) -> None:
        self.selected_image = image_path
        self.image_label_var.set(str(image_path))
        self.log(f"Selected image: {image_path}")
        self.output_data = None
        self.save_button.config(state="disabled")
        self.display_details(image_path)
        self.display_image_preview(image_path)
        self.clear_output()
        self.update_status("Image selected. Ready to run.", 0)

    def display_details(self, image_path: Path) -> None:
        details = [f"Path: {image_path}"]
        if image_path.exists():
            details.append(f"Size: {image_path.stat().st_size / 1024:.1f} KB")
            details.append(f"Preview: {'Enabled' if PIL_AVAILABLE else 'Install Pillow for preview'}")
        details.append(f"Saved JSON: {self.output_path}")

        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", END)
        self.details_text.insert(END, "\n".join(details))
        self.details_text.configure(state="disabled")

    def display_image_preview(self, image_path: Path) -> None:
        self.preview_canvas.delete("all")
        if not PIL_AVAILABLE:
            self.preview_canvas.create_text(
                16,
                16,
                anchor=NW,
                text="Install Pillow to enable live image preview.",
                fill="#555",
                font=("Segoe UI", 11),
                tags="placeholder",
            )
            return

        try:
            image = Image.open(image_path)
            max_width, max_height = 520, 380
            image.thumbnail((max_width, max_height), Image.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(image)
            self.preview_canvas.create_image(16, 16, anchor=NW, image=self.preview_image)
        except Exception as error:
            self.preview_canvas.create_text(
                16,
                16,
                anchor=NW,
                text=f"Preview unavailable:\n{error}",
                fill="#b00",
                font=("Segoe UI", 10),
                tags="placeholder",
            )

    def run_pipeline_from_gui(self) -> None:
        if self.selected_image is None:
            messagebox.showwarning("No image selected", "Please select a diagram image first.")
            return

        self.run_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.update_status("Running pipeline...", 10)
        self.log(f"Pipeline started for {self.selected_image}")
        self.clear_output()

        try:
            result = run_pipeline(str(self.selected_image))
            self.output_data = result
            save_json(result, self.output_path)
            self.display_json(result)
            self.display_summary(result)
            self.save_button.config(state="normal")
            self.update_status(f"Pipeline completed. Saved to {self.output_path}", 100)
            self.log("Pipeline completed successfully.")
            messagebox.showinfo("Success", f"Pipeline completed and output saved to:\n{self.output_path}")
        except Exception as error:
            self.update_status("Pipeline failed", 0)
            self.log(f"Pipeline error: {error}")
            self.log(traceback.format_exc())
            messagebox.showerror("Pipeline error", str(error))
        finally:
            self.run_button.config(state="normal")

    def clear_output(self) -> None:
        for widget in (self.json_text, self.summary_text):
            widget.configure(state="normal")
            widget.delete("1.0", END)
            widget.configure(state="disabled")

    def display_json(self, result: dict) -> None:
        self.json_text.configure(state="normal")
        self.json_text.delete("1.0", END)
        self.json_text.insert(END, json.dumps(result, indent=2))
        self.json_text.configure(state="disabled")

    def display_summary(self, result: dict) -> None:
        metadata = result.get("metadata", {})
        lines = ["Diagram Summary", "" + "=" * 40, f"Image: {metadata.get('source', self.selected_image.name if self.selected_image else 'N/A')}"]
        lines.append(f"Blocks: {len(result.get('blocks', []))}")
        lines.append(f"Text items: {len(result.get('text', []))}")
        lines.append(f"Connections: {len(result.get('connections', []))}")
        lines.append("")
        lines.append("Detected blocks:")
        for block in result.get("blocks", [])[:12]:
            lines.append(f"  • {block.get('id')} | {block.get('type')} | {block.get('label')}")

        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", END)
        self.summary_text.insert(END, "\n".join(lines))
        self.summary_text.configure(state="disabled")
        self.update_stats(result)

    def update_stats(self, result: dict) -> None:
        self.stats["image"].configure(text=self.selected_image.name if self.selected_image else "N/A")
        self.stats["blocks"].configure(text=str(len(result.get("blocks", []))))
        self.stats["text"].configure(text=str(len(result.get("text", []))))
        self.stats["connections"].configure(text=str(len(result.get("connections", []))))

    def save_output_as(self) -> None:
        if self.output_data is None:
            messagebox.showwarning("No output available", "Run the pipeline before saving output.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save output JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="diagram_output.json",
        )
        if file_path:
            save_json(self.output_data, Path(file_path))
            self.update_status(f"Output saved to {file_path}", 100)
            self.log(f"Output exported to {file_path}")
            messagebox.showinfo("Saved", f"Output JSON saved to:\n{file_path}")

    def copy_json_to_clipboard(self) -> None:
        if self.output_data is None:
            messagebox.showwarning("Nothing to copy", "Generate output before copying JSON.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(json.dumps(self.output_data, indent=2))
        self.update_status("JSON copied to clipboard", 100)
        self.log("JSON copied to clipboard.")


def main() -> None:
    root = Tk()
    DiagramDigitizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

