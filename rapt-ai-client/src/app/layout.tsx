import * as React from 'react';
import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from '@/theme';
import InitColorSchemeScript from '@mui/material/InitColorSchemeScript';
import ModeSwitch from '@/components/ModeSwitch';
import RaptAppBar from '@/components/RaptAppBar';
import Grid from '@mui/material/Grid2';
import Box from '@mui/material/Box';
import SideMenu from '@/components/SideMenu';
import ClientProvider from '@/components/ClientProvider';

export default function RootLayout(props: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <InitColorSchemeScript attribute="class" />
        <AppRouterCacheProvider options={{ enableCssLayer: true }}>
          <ThemeProvider theme={theme}>
            <ClientProvider>
              {/* CssBaseline kickstart an elegant, consistent, and simple baseline to build upon. */}
              <CssBaseline />
              {/* <ModeSwitch /> */}
              <RaptAppBar />
              <Box sx={{ flexGrow: 1 }}>
                <Grid container spacing={2}>
                  <Grid size={2}>
                    <SideMenu />
                  </Grid>
                  <Grid size={10}>
                    {props.children}
                  </Grid>
                </Grid>
              </Box>
            </ClientProvider>
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
