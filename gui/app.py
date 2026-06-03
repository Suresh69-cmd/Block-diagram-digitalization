import json
import sys
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, Button, Frame, Label, Text, Tk, filedialog, messagebox

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_pipeline
from src.utils.file_io import save_json


class DiagramDigitizerApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Control Diagram Digitizer")
        self.root.geometry("900x600")
        self.selected_image: Path | None = None

        top_bar = Frame(root, padx=12, pady=12)
        top_bar.pack(fill="x")

        self.image_label = Label(top_bar, text="No image selected", anchor="w")
        self.image_label.pack(side=LEFT, fill="x", expand=True)

        browse_button = Button(top_bar, text="Browse Image", command=self.browse_image)
        browse_button.pack(side=RIGHT, padx=(8, 0))

        run_button = Button(top_bar, text="Run Pipeline", command=self.run_pipeline_from_gui)
        run_button.pack(side=RIGHT)

        self.output_text = Text(root, wrap="word", padx=12, pady=12)
        self.output_text.pack(fill=BOTH, expand=True, padx=12, pady=(0, 12))

    def browse_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select diagram image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.selected_image = Path(file_path)
            self.image_label.config(text=str(self.selected_image))

    def run_pipeline_from_gui(self) -> None:
        if self.selected_image is None:
            messagebox.showwarning("No image selected", "Please select a diagram image first.")
            return

        try:
            result = run_pipeline(str(self.selected_image))
            output_path = PROJECT_ROOT / "data" / "output" / "latest_output.json"
            save_json(result, output_path)
        except Exception as error:
            messagebox.showerror("Pipeline error", str(error))
            return

        self.output_text.delete("1.0", END)
        self.output_text.insert(END, json.dumps(result, indent=2))
        messagebox.showinfo("Success", f"Output saved to {output_path}")


def main() -> None:
    root = Tk()
    DiagramDigitizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

