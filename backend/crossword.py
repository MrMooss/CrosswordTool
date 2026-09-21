import base64
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class Crossword:
    def __init__(self, url: str):
        self.url = url

        response = requests.get(url)
        response.raise_for_status()

        self.response = response
        self.cell_size = 30


    def save_pdf(self, svg, filename="crossword.pdf"):
        viewbox = [
            float(value)
            for value in svg["viewBox"].split()
        ]

        _, _, width, height = viewbox

        svg_string = str(svg)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @page {{
                    size: {width}px {height}px;
                    margin: 0;
                }}

                html, body {{
                    margin: 0;
                    padding: 0;
                    width: {width}px;
                    height: {height}px;
                }}

                svg {{
                    display: block;
                    width: {width}px;
                    height: {height}px;
                }}
            </style>
        </head>
        <body>
            {svg_string}
        </body>
        </html>
        """

        with sync_playwright() as p:
            browser = p.chromium.launch()

            page = browser.new_page()
            page.set_content(html)

            page.pdf(
                path=filename,
                width=f"{width}px",
                height=f"{height}px",
                margin={
                    "top": "0",
                    "right": "0",
                    "bottom": "0",
                    "left": "0",
                },
                print_background=True,
            )

            browser.close()
        
    def render(self):
        svg = self._get_svg()

        title = self._get_title()
        self._put_title_in_empty_area(svg, title)

        # eredeti számok törlése
        for text in svg.find_all("text", class_="cx-c"):
            text.decompose()

        
        # új számok megtervezése
        number_places = self._plan_number_places()

        # új számok hozzáadása
        for number, row, col, x, y in number_places:
            text = svg.new_tag(
                "text",
                attrs={
                    "class": "cx-c",
                    "x": str(x),
                    "y": str(y),
                    "dy": "1em",
                    "font-family": "Arial"
                }
            )
            text.string = number
            svg.append(text)

        style = svg.find("style")

        style.string += """
        .cx-c {
            font-size: 24px;
        }
        """

        old_viewbox = [float(value) for value in svg["viewbox"].split()]

        old_viewbox[0] -= 50
        old_viewbox[1] -= 50
        old_viewbox[2] += 50
        old_viewbox[3] += 50

        del svg["viewbox"]
        svg["viewBox"] = " ".join(map(str, old_viewbox))

        return svg

    def _find_largest_empty_area(self, svg):
        """
        Find the largest empty rectangular area inside the SVG viewBox.

        Returns:
            tuple: (x, y, width, height, area)
        """

        viewbox = [float(value) for value in svg["viewbox"].split()]
        vx, vy, vw, vh = viewbox

        occupied = []

        for rect in svg.find_all("rect"):
            x = float(rect.get("x", 0))
            y = float(rect.get("y", 0))
            width = float(rect.get("width", 0))
            height = float(rect.get("height", 0))

            occupied.append((x, y, width, height))

        # Minden lehetséges x és y határpont
        xs = sorted({
            vx,
            vx + vw,
            *[x for x, y, w, h in occupied],
            *[x + w for x, y, w, h in occupied],
        })

        ys = sorted({
            vy,
            vy + vh,
            *[y for x, y, w, h in occupied],
            *[y + h for x, y, w, h in occupied],
        })

        best = None

        for i, x1 in enumerate(xs[:-1]):
            for x2 in xs[i + 1:]:
                width = x2 - x1

                for j, y1 in enumerate(ys[:-1]):
                    for y2 in ys[j + 1:]:
                        height = y2 - y1
                        area = width * height

                        if best is not None and area <= best[4]:
                            continue

                        collision = False

                        for rx, ry, rw, rh in occupied:
                            if (
                                x1 < rx + rw
                                and x2 > rx
                                and y1 < ry + rh
                                and y2 > ry
                            ):
                                collision = True
                                break

                        if not collision:
                            best = (
                                x1,
                                y1,
                                width,
                                height,
                                area,
                            )

        return best

    def _put_title_in_empty_area(self, svg, title):
        """
        Put the title in the largest empty area of the SVG.

        Args:
            svg (BeautifulSoup): The SVG content.
            title (str): The title to put in the empty area.
        """
        largest_area = self._find_largest_empty_area(svg)

        if largest_area is None:
            return

        x, y, width, height, area = largest_area

        text = svg.new_tag(
            "text",
            attrs={
                "x": str(x + width / 2),
                "y": str(y + height / 2),
                "text-anchor": "middle",
                "dominant-baseline": "middle",
                "font-size": "40px",
                "font-family": "Arial",
                "font-weight": "bold",
            }
        )
        text.string = title
        svg.append(text)

    def _get_title(self):
        """
        Get the title of the crossword from the HTML content.

        Returns:
            str: The title of the crossword.
        """
        soup = BeautifulSoup(self.response.content, "html.parser")
        title_tag = soup.find("h1")
        if title_tag:
            return title_tag.text.strip()
        return "Crossword"

    def _get_svg(self):
        """
        Get the SVG content.

        """
        soup = BeautifulSoup(self.response.content, "html.parser")

        svg = soup.find("svg")

        return svg

    def _get_all_cells(self, svg: BeautifulSoup):
        """
        Get all the cells in the SVG.
        """
        cells = {}
        for square in svg.find_all("g"):
            row, col = square.get("id").split("-")[1:]
            coords = square.find("rect")
            if coords:
                x = float(coords.get("x"))
                y = float(coords.get("y"))
            cells[(int(row), int(col))] = (x, y)
        return cells

    def _find_numbers_in_svg(self, svg: BeautifulSoup):
        """
        Find numbers and their positions in an SVG.
        """
        numbers = []
        for square in svg.find_all("g"):
            number = square.find("text", class_="cx-c")
            if number:
                row, col = square.get("id").split("-")[1:]
                x = float(number.get("x"))
                if x > 0:
                    x = x-2
                y = float(number.get("y"))
                if y > 0:
                    y = y-2
                numbers.append((number.text.strip(), int(row), int(col), x, y))
        return numbers


    def _number_type(self, number: int) -> str:
        """
        Gets the clue for a given number.

        Returns:
            str: "a" for across, "d" for down, "b" for "both".
        """
        soup = BeautifulSoup(self.response.content, "html.parser")

        across_div = soup.find("div", id="across-box")
        across_clues = self._get_cluesnums_form_div(across_div)

        down_div = soup.find("div", id="down-box")
        down_clues = self._get_cluesnums_form_div(down_div)

        if number in across_clues:
            if number in down_clues:
                return "b"
            return "a"
        return "d"

    def _get_cluesnums_form_div(self, div_element: BeautifulSoup):
        """
        Gets the clues from a div.
        """
        clue_numbers = []
        for clue in div_element.find_all("li"):
            strong = clue.find("strong")
            clue_numbers.append(int(strong.text.strip('.')))
        return clue_numbers

    def _plan_number_places(self):
        """
        Plan out the number places in the crossword grid.
        """
        svg = self._get_svg()
        numbers = self._find_numbers_in_svg(svg)
        cells = self._get_all_cells(svg)

        number_places = []
        for number in numbers:
            number_value, row, col, x, y = number
            number_type = self._number_type(int(number_value))

            if number_type == "a":
                coll, index = self._find_collision(number_places, row, col-1)
                if coll:
                    if len(number_value) == 1:
                        number_place = number_places[index]
                        number_places[index] = (number_place[0], number_place[1], number_place[2], number_place[3]+5, number_place[4])
                        number_places.append((number_value, row, col-1, x-30, y+6))
                    else:
                        number_place = number_places[index]
                        number_places[index] = (number_place[0], number_place[1], number_place[2], number_place[3]-10, number_place[4]+5)
                        number_places.append((number_value, row, col-1, x-30, y+10))
                else:
                    if len(number_value) == 1:
                        number_places.append((number_value, row, col-1, x-15, y))
                    else:
                        number_places.append((number_value, row, col-1, x-30, y))
            elif number_type == "d":
                coll, index = self._find_collision(number_places, row-1, col)
                if coll:
                    if len(number_value) == 1:
                        number_place = number_places[index]
                        number_places[index] = (number_place[0], number_place[1], number_place[2], number_place[3], number_place[4]-2)
                        number_places.append((number_value, row-1, col, x-2, y-12))
                    else:
                        number_place = number_places[index]
                        number_places[index] = (number_place[0], number_place[1], number_place[2], number_place[3], number_place[4]-15)
                        number_places.append((number_value, row-1, col, x-15, y-25))
                else:
                    if len(number_value) == 1:
                        number_places.append((number_value, row-1, col, x+7, y-27))
                    else:
                        number_places.append((number_value, row-1, col, x+1, y-27))
            elif number_type == "b":
                coll, index = self._find_collision(number_places, row-1, col)
                if coll:
                    number_places.append((number_value, row-1, col, x-26, y-28))
                else:
                    if (row-1, col-1) in cells:
                        if len(number_value) == 1:
                            number_places.append((number_value, row-1, col, x, y-28))
                        else:
                            number_places.append((number_value, row-1, col, x, y-28))
                    else:
                        if len(number_value) == 1:
                            number_places.append((number_value, row-1, col, x-10, y-28))
                        else:
                            number_places.append((number_value, row-1, col, x-20, y-28))
        return number_places

    def _find_collision(self, number_places, row, col):
        for i, place in enumerate(number_places):
            if place[1] == row and place[2] == col:
                return True, i

        return False, None