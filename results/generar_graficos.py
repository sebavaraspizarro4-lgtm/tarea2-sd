import json
import matplotlib.pyplot as plt
import numpy as np

# Datos de los escenarios
escenarios = {
    "Base\n(1 consumer)": {"hit_rate": 0.8034, "p50": 7.76, "p95": 67.39, "avg": 11.65, "total": 1109},
    "Fallas\n30%":        {"hit_rate": 0.6848, "p50": 7.86, "p95": 74.68, "avg": 18.27, "total": 1104},
    "3 Consumers":        {"hit_rate": 0.8067, "p50": 7.55, "p95": 66.75, "avg": 11.48, "total": 1107},
    "Spike\n3000q":       {"hit_rate": 0.9237, "p50": 7.02, "p95": 14.89, "avg": 7.56,  "total": 3119},
}

nombres = list(escenarios.keys())
hit_rates = [v["hit_rate"]*100 for v in escenarios.values()]
p50 = [v["p50"] for v in escenarios.values()]
p95 = [v["p95"] for v in escenarios.values()]
avg = [v["avg"] for v in escenarios.values()]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("Comparación de Escenarios - Tarea 2 Sistemas Distribuidos", fontsize=13, fontweight="bold")

# Gráfico 1: Hit Rate
colors = ["#2196F3", "#F44336", "#4CAF50", "#FF9800"]
bars = axes[0].bar(nombres, hit_rates, color=colors, edgecolor="black", linewidth=0.5)
axes[0].set_title("Hit Rate por Escenario")
axes[0].set_ylabel("Hit Rate (%)")
axes[0].set_ylim(0, 100)
for bar, val in zip(bars, hit_rates):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{val:.1f}%", ha="center", fontsize=9, fontweight="bold")

# Gráfico 2: Latencia p50 y p95
x = np.arange(len(nombres))
w = 0.35
axes[1].bar(x - w/2, p50, w, label="p50", color="#42A5F5", edgecolor="black", linewidth=0.5)
axes[1].bar(x + w/2, p95, w, label="p95", color="#EF5350", edgecolor="black", linewidth=0.5)
axes[1].set_title("Latencia p50 y p95 (ms)")
axes[1].set_ylabel("Latencia (ms)")
axes[1].set_xticks(x)
axes[1].set_xticklabels(nombres)
axes[1].legend()

# Gráfico 3: Latencia promedio
bars3 = axes[2].bar(nombres, avg, color=colors, edgecolor="black", linewidth=0.5)
axes[2].set_title("Latencia Promedio (ms)")
axes[2].set_ylabel("Latencia (ms)")
for bar, val in zip(bars3, avg):
    axes[2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f"{val:.1f}ms", ha="center", fontsize=9, fontweight="bold")

plt.tight_layout()
plt.savefig("graficos_escenarios.png", dpi=150, bbox_inches="tight")
print("Grafico guardado: graficos_escenarios.png")
