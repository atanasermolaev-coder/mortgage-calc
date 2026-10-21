"""tkinter-версия калькулятора. Запускается только локально:  python -m app.gui

На сервере (Ubuntu Server без GUI) и в CI этот файл не используется.
"""
import tkinter as tk
from tkinter import messagebox

from app.mortgage import monthly_payment, overpayment, total_payment


def main() -> None:
    root = tk.Tk()
    root.title("Калькулятор ипотеки")

    fields = [("Сумма кредита, руб.", "3000000"),
              ("Ставка, % годовых", "12"),
              ("Срок, лет", "20")]
    entries = []
    for row, (text, default) in enumerate(fields):
        tk.Label(root, text=text).grid(row=row, column=0, padx=8, pady=6, sticky="w")
        entry = tk.Entry(root)
        entry.insert(0, default)
        entry.grid(row=row, column=1, padx=8, pady=6)
        entries.append(entry)
    entry_p, entry_r, entry_y = entries

    result = tk.Label(root, text="", justify="left")
    result.grid(row=4, column=0, columnspan=2, pady=8)

    def calculate() -> None:
        try:
            args = (float(entry_p.get()), float(entry_r.get()), int(entry_y.get()))
            result.config(text=(
                f"Платёж: {monthly_payment(*args):,.2f} / мес.\n"
                f"Всего выплат: {total_payment(*args):,.2f}\n"
                f"Переплата: {overpayment(*args):,.2f}"
            ))
        except ValueError as exc:
            messagebox.showerror("Ошибка", f"Проверьте введённые данные:\n{exc}")

    tk.Button(root, text="Рассчитать", command=calculate).grid(
        row=3, column=0, columnspan=2, pady=8)
    root.mainloop()


if __name__ == "__main__":
    main()
