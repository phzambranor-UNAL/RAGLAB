def saludar_estudiante(nombre):
    return f"Bienvenido, {nombre}. Ya estás listo para construir proyectos en Python."


def calcular_total(sesiones, horas_por_sesion):
    return sesiones * horas_por_sesion


def calcular_progreso(completados, total):
    """Retorna el porcentaje completado (0–100). Si total es 0, retorna 0."""
    if total == 0:
        return 0
    return (completados / total) * 100


nombre_estudiante = "PPDRP"

print(saludar_estudiante(nombre_estudiante))
print("Horas del módulo:", calcular_total(11.3, 10))

# Ejemplos de uso de calcular_progreso
print("Progreso (7 de 10):", calcular_progreso(7, 10))    # 70.0
print("Progreso (0 de 5):", calcular_progreso(0, 5))      # 0.0
print("Progreso (10 de 10):", calcular_progreso(10, 10))  # 100.0
