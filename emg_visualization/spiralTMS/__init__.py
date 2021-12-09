import math
import random
import numpy as np
from sys import exit
import xlsxwriter as xlsx
from matplotlib import pyplot as plt


def info(data):
    print(f'\n****************** INFO ******************\n'
          f'Maximium stimulation radius: {data[0]:.2f} mm\n'
          f'Distance between stimulated spots: {data[1]} mm\n'
          f'Delta: {data[2]} mm/rad\n'
          f'Number of stimulated spots: {data[3]}\n'
          f'******************************************')


def ellipse_path(
        x_hotspot,
        y_hotspot,
        z=139.056,
        e=0.85,
        size=40,
        distance=20,
        delta=1.25,
        phi=0):
    x_values = np.array([x_hotspot])
    y_values = np.array([y_hotspot])
    x_marker_values = np.array([x_hotspot])
    y_marker_values = np.array([y_hotspot])

    b = np.sqrt(1 - e ** 2)
    delta_angle = (np.pi / 100)
    delta_param = delta * delta_angle
    param = 0
    angle = 0

    counter = 1
    while True:
        if counter == 1:
            x2 = x_hotspot
            y2 = y_hotspot
        else:
            x2 = x_marker_values[-1]
            y2 = y_marker_values[-1]
        x = param * np.cos(angle + phi) + x_hotspot
        y = b * param * np.sin(angle + phi) + y_hotspot
        x_values = np.append(x_values, x)
        y_values = np.append(y_values, y)

        radius = np.sqrt((x - x_hotspot) ** 2 + (y - y_hotspot) ** 2)

        if angle < np.deg2rad(850):
            if (distance / 3) < np.sqrt((y2 - y) ** 2 + (x2 - x) ** 2):
                x_marker_values = np.append(x_marker_values, x)
                y_marker_values = np.append(y_marker_values, y)
                counter += 1
        else:
            if distance < np.sqrt((y2 - y) ** 2 + (x2 - x) ** 2):
                x_marker_values = np.append(x_marker_values, x)
                y_marker_values = np.append(y_marker_values, y)
                counter += 1

        if radius >= size:
            break

        param += delta_param
        angle += delta_angle

    data_array = [radius, distance, delta, counter]

    z_marker_values = np.full_like(x_marker_values, z)
    zero_values = np.full_like(x_marker_values, 0.000)
    one_values = np.full_like(x_marker_values, 1.000)
    two_values = np.full_like(x_marker_values, 2.000)

    export_array = np.transpose(np.array([
        x_marker_values,
        y_marker_values,
        z_marker_values,
        zero_values,
        zero_values,
        zero_values,
        one_values,
        one_values,
        zero_values,
        two_values]))

    np.savetxt('elliptical_spiral.mks', export_array, fmt='%s')
    return x_marker_values, y_marker_values, x_values, y_values, data_array


def ellipse_sim(
        x_hotspot,
        y_hotspot,
        size=60,
        distance=20,
        delta=1.5,
        phi=0):
    x_values = np.array([x_hotspot])
    y_values = np.array([y_hotspot])
    x_marker_values = np.array([x_hotspot])
    y_marker_values = np.array([y_hotspot])
    x_marker_values_stim = np.array([x_hotspot])
    y_marker_values_stim = np.array([y_hotspot])
    stim_values = np.array([])
    x_marker_all = np.array([x_hotspot])
    y_marker_all = np.array([y_hotspot])

    delta_angle = (np.pi / 100)
    delta_param = delta * delta_angle
    param = 0
    angle = 0
    counter = 1
    stop_angle = 0

    while True:
        if counter == 1:
            x2 = x_hotspot
            y2 = y_hotspot
        x = 2 * param * np.cos(angle + phi) + x_hotspot
        y = param * np.sin(angle + phi) + y_hotspot

        x_values = np.append(x_values, x)
        y_values = np.append(y_values, y)

        radius = np.sqrt((x - x_hotspot) ** 2 + (y - y_hotspot) ** 2)

        if angle < np.deg2rad(675):
            if (distance / 2) < np.sqrt((y2 - y) ** 2 + (x2 - x) ** 2):
                stim = random.uniform(5000 / radius, 50000 / radius)
                stim_values = np.append(stim_values, stim)
                if stim >= 50:
                    x_marker_values_stim = np.append(x_marker_values_stim, x)
                    x_marker_all = np.append(x_marker_all, x)
                    y_marker_values_stim = np.append(y_marker_values_stim, y)
                    y_marker_all = np.append(y_marker_all, y)
                    x2 = x_marker_values_stim[-1]
                    y2 = y_marker_values_stim[-1]
                    counter += 1
                else:
                    x_marker_values = np.append(x_marker_values, x)
                    x_marker_all = np.append(x_marker_all, x)
                    y_marker_values = np.append(y_marker_values, y)
                    y_marker_all = np.append(y_marker_all, y)
                    x2 = x_marker_values[-1]
                    y2 = y_marker_values[-1]
                    counter += 1

        elif distance < np.sqrt((y2 - y) ** 2 + (x2 - x) ** 2):
            if radius <= 60:
                stim = random.uniform(0 / radius, 5000 / radius)
            else:
                stim = random.uniform(0 / radius, 100 / radius)

            stim_values = np.append(stim_values, stim)
            if stim >= 50:
                x_marker_values_stim = np.append(x_marker_values_stim, x)
                x_marker_all = np.append(x_marker_all, x)
                y_marker_values_stim = np.append(y_marker_values_stim, y)
                y_marker_all = np.append(y_marker_all, y)
                x2 = x_marker_values_stim[-1]
                y2 = y_marker_values_stim[-1]
                stop_angle = 0
                counter += 1

            else:
                angle_vectors = np.abs(np.arccos(np.dot(
                    [x - x_hotspot, y - y_hotspot] / np.linalg.norm([x - x_hotspot, y - y_hotspot]),
                    [x2 - x_hotspot, y2 - y_hotspot] / np.linalg.norm([x2 - x_hotspot, y2 - y_hotspot]))))
                x_marker_values = np.append(x_marker_values, x)
                x_marker_all = np.append(x_marker_all, x)
                y_marker_values = np.append(y_marker_values, y)
                y_marker_all = np.append(y_marker_all, y)
                x2 = x_marker_values[-1]
                y2 = y_marker_values[-1]
                stop_angle += angle_vectors
                counter += 1

        param += delta_param
        angle += delta_angle

        if stop_angle >= np.deg2rad(360) or radius >= size:
            break

    data_array = [radius, distance, delta, counter]

    return x_marker_values_stim, y_marker_values_stim, x_marker_values, y_marker_values, x_values, y_values, data_array


def circle_path(
        x_hotspot,
        y_hotspot,
        z=139.056,
        size=60,
        distance=20,
        delta=1.5,
        phi=0):

    x_values = np.array([x_hotspot])
    y_values = np.array([y_hotspot])
    x_marker_values = np.array([x_hotspot])
    y_marker_values = np.array([y_hotspot])

    delta_angle = (np.pi / 100)
    delta_param = delta * delta_angle
    param = 0
    angle = 0

    counter = 1
    while True:
        if counter == 1:
            x2 = x_hotspot
            y2 = y_hotspot
        else:
            x2 = x_marker_values[-1]
            y2 = y_marker_values[-1]
        x = (param * np.cos(angle + phi)) + x_hotspot
        y = (param * np.sin(angle + phi)) + y_hotspot
        x_values = np.append(x_values, x)
        y_values = np.append(y_values, y)

        radius = np.sqrt((x - x_hotspot) ** 2 + (y - y_hotspot) ** 2)

        if angle < np.deg2rad(675):
            if (distance / 3) < np.sqrt((y2 - y) ** 2 + (x2 - x) ** 2):
                x_marker_values = np.append(x_marker_values, x)
                y_marker_values = np.append(y_marker_values, y)
                counter += 1
        else:
            if distance < np.sqrt((y2 - y) ** 2 + (x2 - x) ** 2):
                x_marker_values = np.append(x_marker_values, x)
                y_marker_values = np.append(y_marker_values, y)
                counter += 1

        if radius >= size:
            break

        param += delta_param
        angle += delta_angle

    data_array = [radius, distance, delta, counter]

    z_marker_values = np.full_like(x_marker_values, z)
    zero_values = np.full_like(x_marker_values, 0.000)
    one_values = np.full_like(x_marker_values, 1.000)
    two_values = np.full_like(x_marker_values, 2.000)

    export_array = np.transpose(np.array([
        x_marker_values,
        y_marker_values,
        z_marker_values,
        zero_values,
        zero_values,
        zero_values,
        one_values,
        one_values,
        zero_values,
        two_values]))

    np.savetxt('circular_spiral.mks', export_array, fmt='%s')

    return x_marker_values, y_marker_values, x_values, y_values, data_array


def circle_sim(
        x_hotspot,
        y_hotspot,
        size=60,
        distance=20,
        delta=1.5,
        phi=0):

    x_values = np.array([x_hotspot])
    y_values = np.array([y_hotspot])
    x_marker_values = np.array([x_hotspot])
    y_marker_values = np.array([y_hotspot])
    x_marker_values_stim = np.array([x_hotspot])
    y_marker_values_stim = np.array([y_hotspot])
    stim_values = np.array([])
    x_marker_all = np.array([x_hotspot])
    y_marker_all = np.array([y_hotspot])

    delta_angle = (np.pi / 100)
    delta_param = delta * delta_angle
    param = 0
    angle = 0
    counter = 1
    stop_angle = 0

    while True:
        if counter == 1:
            x2 = x_hotspot
            y2 = y_hotspot
        x = (param * np.cos(angle + phi)) + x_hotspot
        y = (param * np.sin(angle + phi)) + y_hotspot

        x_values = np.append(x_values, x)
        y_values = np.append(y_values, y)

        radius = np.sqrt((x - x_hotspot) ** 2 + (y - y_hotspot) ** 2)

        if angle < np.deg2rad(675):
            if (distance / 2) < np.sqrt((y2 - y) ** 2 + (x2 - x) ** 2):
                stim = random.uniform(5000 / radius, 50000 / radius)
                stim_values = np.append(stim_values, stim)
                if stim >= 50:
                    x_marker_values_stim = np.append(x_marker_values_stim, x)
                    x_marker_all = np.append(x_marker_all, x)
                    y_marker_values_stim = np.append(y_marker_values_stim, y)
                    y_marker_all = np.append(y_marker_all, y)
                    x2 = x_marker_values_stim[-1]
                    y2 = y_marker_values_stim[-1]
                    counter += 1
                else:
                    x_marker_values = np.append(x_marker_values, x)
                    x_marker_all = np.append(x_marker_all, x)
                    y_marker_values = np.append(y_marker_values, y)
                    y_marker_all = np.append(y_marker_all, y)
                    x2 = x_marker_values[-1]
                    y2 = y_marker_values[-1]
                    counter += 1

        elif distance < np.sqrt((y2 - y) ** 2 + (x2 - x) ** 2):
            if radius <= 60:
                stim = random.uniform(0 / radius, 5000 / radius)
            else:
                stim = random.uniform(0 / radius, 100 / radius)

            stim_values = np.append(stim_values, stim)
            if stim >= 50:
                x_marker_values_stim = np.append(x_marker_values_stim, x)
                x_marker_all = np.append(x_marker_all, x)
                y_marker_values_stim = np.append(y_marker_values_stim, y)
                y_marker_all = np.append(y_marker_all, y)
                x2 = x_marker_values_stim[-1]
                y2 = y_marker_values_stim[-1]
                stop_angle = 0
                counter += 1

            else:
                angle_vectors = np.abs(np.arccos(np.dot(
                    [x - x_hotspot, y - y_hotspot] / np.linalg.norm([x - x_hotspot, y - y_hotspot]),
                    [x2 - x_hotspot, y2 - y_hotspot] / np.linalg.norm([x2 - x_hotspot, y2 - y_hotspot]))))
                x_marker_values = np.append(x_marker_values, x)
                x_marker_all = np.append(x_marker_all, x)
                y_marker_values = np.append(y_marker_values, y)
                y_marker_all = np.append(y_marker_all, y)
                x2 = x_marker_values[-1]
                y2 = y_marker_values[-1]
                stop_angle += angle_vectors
                counter += 1

        param += delta_param
        angle += delta_angle

        if stop_angle >= np.deg2rad(360) or radius >= size:
            break

    data_array = [radius, distance, delta, counter]

    workbook = xlsx.Workbook('stim_coordinates.xlsx')
    worksheet = workbook.add_worksheet('Imported Data')
    worksheet.write('A1', "X [mm]")
    worksheet.write('B1', 'Y [mm]')
    worksheet.write('C1', 'Stimulation [uV]')

    row = 1
    for x in x_marker_all:
        worksheet.write(row, 0, x)
        row += 1
    row = 1
    for y in y_marker_all:
        worksheet.write(row, 1, y)
        row += 1
    row = 1
    for s in stim_values:
        worksheet.write(row, 2, s)
        row += 1
    workbook.close()

    return x_marker_values_stim, y_marker_values_stim, x_marker_values, y_marker_values, x_values, y_values, data_array


def heatmap(
        x_hotspot,
        y_hotspot,
        shape='e',
        grid_size=1,
        h=30):

    if shape == 'c':
        x, y, x2, y2, x3, y3, _ = circle_sim(x_hotspot, y_hotspot)
    if shape == 'e':
        x, y, x2, y2, x3, y3, _ = ellipse_sim(x_hotspot, y_hotspot)
    else:
        print(f"Please specify the shape to be used on the spiral. 'e' for elliptical and 'c' for circular.")
        exit()

    # GETTING X,Y MIN AND MAX
    x_min = min(x)
    x_max = max(x)
    y_min = min(y)
    y_max = max(y)

    # CONSTRUCT GRID
    x_grid = np.arange(x_min - h, x_max + h, grid_size)
    y_grid = np.arange(y_min - h, y_max + h, grid_size)
    x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)

    # GRID CENTER POINT
    xc = x_mesh + (grid_size / 2)
    yc = y_mesh + (grid_size / 2)

    # FUNCTION TO CALCULATE INTENSITY WITH QUARTIC KERNEL
    def kde_quartic(da, ha):
        dn = da / ha
        P = (15 / 16) * (1 - dn ** 2) ** 2
        return P

    # PROCESSING
    intensity_list = []
    for j in range(len(xc)):
        intensity_row = []
        for k in range(len(xc[0])):
            kde_value_list = []
            for i in range(len(x)):
                # CALCULATE DISTANCE
                d = math.sqrt((xc[j][k] - x[i]) ** 2 + (yc[j][k] - y[i]) ** 2)
                if d <= h:
                    p = kde_quartic(d, h)
                else:
                    p = 0
                kde_value_list.append(p)
            # SUM ALL INTENSITY VALUE
            p_total = sum(kde_value_list)
            intensity_row.append(p_total)
        intensity_list.append(intensity_row)

    # HEATMAP OUTPUT
    intensity = np.array(intensity_list)
    plt.pcolormesh(x_mesh, y_mesh, intensity, cmap='jet', shading='auto')
    plt.plot(x3, y3, color='k', linewidth=0.5, label='TMS coil path')
    plt.scatter(x2, y2, color='b', label='TMS stimulation < 50 uV')
    plt.scatter(x, y, color='r', label='TMS stimulation > 50 uV')
    plt.legend()
    plt.show()

    return x, y, x2, y2, x3, y3
