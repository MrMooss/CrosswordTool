import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

from forntend.move_numbers import Crossword


class CrosswordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crossword → PDF")
        self.root.geometry("720x430")
        self.root.minsize(620, 380)

        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar()

        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Card
        style.configure(
            "Card.TFrame",
            background="#ffffff",
        )

        # Title
        style.configure(
            "Title.TLabel",
            background="#ffffff",
            foreground="#111827",
            font=("Segoe UI", 24, "bold"),
        )

        # Subtitle
        style.configure(
            "Subtitle.TLabel",
            background="#ffffff",
            foreground="#6b7280",
            font=("Segoe UI", 10),
        )

        # Labels
        style.configure(
            "Label.TLabel",
            background="#ffffff",
            foreground="#374151",
            font=("Segoe UI", 10, "bold"),
        )

        # Inputs
        style.configure(
            "TEntry",
            padding=10,
            font=("Segoe UI", 10),
        )

        # Status
        style.configure(
            "Status.TLabel",
            background="#ffffff",
            foreground="#6b7280",
            font=("Segoe UI", 9),
        )

    def _build_ui(self):
        self.root.configure(
            background="#eef1f5"
        )

        # Outer area
        outer = tk.Frame(
            self.root,
            bg="#eef1f5",
        )

        outer.pack(
            fill="both",
            expand=True,
            padx=50,
            pady=45,
        )

        # White card
        card = tk.Frame(
            outer,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#e1e5eb",
        )

        card.pack(
            fill="both",
            expand=True,
        )

        # Content inside card
        content = tk.Frame(
            card,
            bg="#ffffff",
        )

        content.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=35,
        )

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        ttk.Label(
            content,
            text="Crossword → PDF",
            style="Title.TLabel",
        ).pack(
            anchor="w"
        )

        ttk.Label(
            content,
            text="Alakítsd át a keresztrejtvényt PDF formátumba.",
            style="Subtitle.TLabel",
        ).pack(
            anchor="w",
            pady=(6, 32),
        )

        # ---------------------------------------------------------
        # URL
        # ---------------------------------------------------------

        ttk.Label(
            content,
            text="Keresztrejtvény URL",
            style="Label.TLabel",
        ).pack(
            anchor="w"
        )

        url_entry = ttk.Entry(
            content,
            textvariable=self.url_var,
        )

        url_entry.pack(
            fill="x",
            pady=(8, 24),
            ipady=4,
        )

        # ---------------------------------------------------------
        # Output
        # ---------------------------------------------------------

        ttk.Label(
            content,
            text="PDF mentési helye",
            style="Label.TLabel",
        ).pack(
            anchor="w"
        )

        output_row = tk.Frame(
            content,
            bg="#ffffff",
        )

        output_row.pack(
            fill="x",
            pady=(8, 30),
        )

        output_entry = ttk.Entry(
            output_row,
            textvariable=self.output_var,
        )

        output_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=4,
        )

        # Browse button
        tk.Button(
            output_row,
            text="Tallózás",
            command=self._choose_output,
            font=("Segoe UI", 10),
            fg="#374151",
            bg="#f3f4f6",
            activeforeground="#111827",
            activebackground="#e5e7eb",
            relief="flat",
            borderwidth=0,
            padx=18,
            pady=9,
            cursor="hand2",
        ).pack(
            side="left",
            padx=(10, 0),
        )

        # ---------------------------------------------------------
        # Generate button
        # ---------------------------------------------------------

        self.generate_button = tk.Button(
            content,
            text="PDF generálása",
            command=self._generate,
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg="#2563eb",
            activeforeground="#ffffff",
            activebackground="#1d4ed8",
            disabledforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=13,
            cursor="hand2",
        )

        self.generate_button.pack(
            fill="x"
        )

        # ---------------------------------------------------------
        # Status
        # ---------------------------------------------------------

        self.status = ttk.Label(
            content,
            text="Készen áll.",
            style="Status.TLabel",
        )

        self.status.pack(
            anchor="w",
            pady=(18, 0),
        )

        url_entry.focus_set()

    # -------------------------------------------------------------
    # File selection
    # -------------------------------------------------------------

    def _choose_output(self):
        path = filedialog.asksaveasfilename(
            title="PDF mentése",
            defaultextension=".pdf",
            filetypes=[
                ("PDF fájl", "*.pdf"),
            ],
            initialfile="crossword.pdf",
        )

        if path:
            self.output_var.set(path)

    # -------------------------------------------------------------
    # Button state
    # -------------------------------------------------------------

    def _set_busy(self, busy):
        if busy:
            self.generate_button.configure(
                state="disabled",
                bg="#93c5fd",
                cursor="arrow",
            )

            self.status.configure(
                text="Generálás folyamatban..."
            )

        else:
            self.generate_button.configure(
                state="normal",
                bg="#2563eb",
                cursor="hand2",
            )

    # -------------------------------------------------------------
    # Generate
    # -------------------------------------------------------------

    def _generate(self):
        url = self.url_var.get().strip()
        output = self.output_var.get().strip()

        # URL ellenőrzés
        if not url:
            messagebox.showwarning(
                "Hiányzó URL",
                "Add meg a keresztrejtvény URL-jét.",
            )
            return

        # Output ellenőrzés
        if not output:
            messagebox.showwarning(
                "Hiányzó mentési hely",
                "Válaszd ki, hova szeretnéd menteni a PDF-et.",
            )
            return

        # .pdf kiterjesztés
        if not output.lower().endswith(".pdf"):
            output += ".pdf"
            self.output_var.set(output)

        self._set_busy(True)

        # A generálás külön threadben fut,
        # hogy ne fagyjon le a GUI.
        threading.Thread(
            target=self._generate_worker,
            args=(url, output),
            daemon=True,
        ).start()

    # -------------------------------------------------------------
    # Worker
    # -------------------------------------------------------------

    def _generate_worker(self, url, output):
        try:
            crossword = Crossword(url)

            # SVG létrehozása
            svg = crossword.render()

            # SVG -> PDF
            crossword.save_pdf(
                svg,
                output,
            )

        except Exception as exc:
            self.root.after(
                0,
                self._generation_failed,
                exc,
            )
            return

        self.root.after(
            0,
            self._generation_finished,
            output,
        )

    # -------------------------------------------------------------
    # Success
    # -------------------------------------------------------------

    def _generation_finished(self, output):
        self._set_busy(False)

        self.status.configure(
            text=f"Elkészült: {output}"
        )

        messagebox.showinfo(
            "Kész",
            f"A PDF sikeresen elkészült.\n\n{output}",
        )

    # -------------------------------------------------------------
    # Error
    # -------------------------------------------------------------

    def _generation_failed(self, exc):
        self._set_busy(False)

        self.status.configure(
            text="Hiba történt a generálás közben."
        )

        messagebox.showerror(
            "Generálási hiba",
            f"{type(exc).__name__}: {exc}",
        )


if __name__ == "__main__":
    root = tk.Tk()

    app = CrosswordApp(root)

    root.mainloop()