/** @type {import('tailwindcss').Config} */
module.exports = {
    dark: 'class',
    content: ['./build/*.html'],
    theme: {
      extend: {
        aspectRatio: {
            '4/3': '4 / 3',
          },
      },
      colors: {
        'main': '#596886',
        'main1': '#052b4a',
        'main2': '#ffd5af',
        'main3': '#ccac8f',
      },
    },
    plugins: [],
  }
  